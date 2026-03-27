#!/usr/bin/env python3
"""Minimal persistent HTTP server for FlipFrame kiosk page."""
import os, sys, signal
from http.server import HTTPServer, SimpleHTTPRequestHandler

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

httpd = HTTPServer(('0.0.0.0', 8765), Handler)
print(f'FlipFrame server on 0.0.0.0:8765 (serving {os.getcwd()})', flush=True)

def stop(*a):
    httpd.shutdown()
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    stop()
