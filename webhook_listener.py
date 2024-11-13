#!/usr/bin/env python3

import hmac
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess

# Load the GitHub secret from an environment variable
GITHUB_SECRET = os.getenv(
    "GITHUB_WEBHOOK_SECRET", ""
).encode()  # Default to an empty byte string if not set


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        signature = self.headers.get("X-Hub-Signature-256")

        # Verify the signature if using a secret
        if GITHUB_SECRET:
            hash_hmac = hmac.new(GITHUB_SECRET, body, hashlib.sha256).hexdigest()
            expected_signature = f"sha256={hash_hmac}"
            if not hmac.compare_digest(expected_signature, signature):
                self.send_response(403)
                self.end_headers()
                return

        data = json.loads(body)

        # Check if push is to 'stage' branch
        if data.get("ref") == "refs/heads/stage":
            self.run_docker_compose_up()

        self.send_response(200)
        self.end_headers()

    def run_docker_compose_up(self):
        subprocess.run(
            ["docker-compose", "-f", "/docker-compose.yml", "up", "--build", "-d"]
        )


def run(server_class=HTTPServer, handler_class=WebhookHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting webhook listener on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
