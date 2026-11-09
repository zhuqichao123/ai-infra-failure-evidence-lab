#!/usr/bin/env python3
"""Minimal, dependency-free HTTP readiness probe for a controlled VM fault lab."""
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

PORT = int(os.environ.get('LISTEN_PORT', '8080'))
if PORT not in (8080, 8081):
    raise SystemExit('LISTEN_PORT must be 8080 or 8081 for this lab')


class Handler(BaseHTTPRequestHandler):
    server_version = 'FailureLabExp01/1.0'
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        path = urlsplit(self.path).path
        if path not in ('/healthz', '/readyz'):
            self._respond(404, {'error': 'not_found', 'path': path})
            return
        self._respond(200, {
            'service': 'failurelab-exp01',
            'status': 'ok',
            'ready': True,
            'port': PORT,
            'path': path,
        })

    def _respond(self, status, data):
        body = (json.dumps(data, sort_keys=True) + '\n').encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        stamp = datetime.now(timezone.utc).isoformat()
        print(stamp, self.client_address[0], fmt % args, flush=True)


if __name__ == '__main__':
    print('Starting failurelab-exp01 on 0.0.0.0:%d' % PORT, flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
