#!/usr/bin/env python3
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32, String


DATA_TIMEOUT_SEC = 1.0


class _Handler(BaseHTTPRequestHandler):
    node = None

    def do_GET(self):
        if self.path == '/data':
            self._json(self.node.get_data())
            return
        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json(self, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass


class MonitorNode(Node):
    def __init__(self):
        super().__init__('r2_monitor_node')
        self._lock = threading.Lock()
        self._latest = {}
        self._seen = {}

        self.create_subscription(PoseStamped, '/odin1/relocation', self._pose_cb, 10)
        self.create_subscription(Float32MultiArray, '/sensor_distances', self._array_cb('sensors'), 10)
        self.create_subscription(Float32MultiArray, '/r0x0121', self._array_cb('r0x0121'), 10)
        self.create_subscription(Int32, '/aruco_comm/tx_id', self._int_cb('aruco'), 10)
        self.create_subscription(String, '/execution_state', self._string_cb('execution_state'), 10)
        self.create_subscription(String, '/active_action', self._string_cb('active_action'), 10)
        self.create_subscription(String, '/last_error', self._string_cb('last_error'), 10)

        _Handler.node = self
        self._httpd = HTTPServer(('0.0.0.0', 8765), _Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.get_logger().info('r2_monitor_node ready on :8765; action APIs removed')

    def _mark(self, key):
        self._seen[key] = time.monotonic_ns()

    def _pose_cb(self, msg):
        q = msg.pose.orientation
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny, cosy)
        with self._lock:
            self._latest['reloc'] = {
                'x': round(msg.pose.position.x * 1000.0, 1),
                'y': round(msg.pose.position.y * 1000.0, 1),
                'yaw_deg': round(yaw * 180.0 / math.pi, 2),
            }
            self._mark('reloc')

    def _array_cb(self, key):
        def cb(msg):
            with self._lock:
                self._latest[key] = [round(float(v), 3) for v in msg.data]
                self._mark(key)
        return cb

    def _int_cb(self, key):
        def cb(msg):
            with self._lock:
                self._latest[key] = int(msg.data)
                self._mark(key)
        return cb

    def _string_cb(self, key):
        def cb(msg):
            with self._lock:
                self._latest[key] = msg.data
                self._mark(key)
        return cb

    def get_data(self):
        now = time.monotonic_ns()
        with self._lock:
            latest = dict(self._latest)
            seen = dict(self._seen)
        latest['online'] = {
            key: (now - t) <= int(DATA_TIMEOUT_SEC * 1e9)
            for key, t in seen.items()
        }
        return latest


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
    try:
        rclpy.spin(node)
    finally:
        node._httpd.shutdown()
        node.destroy_node()
        rclpy.shutdown()
