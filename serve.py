#!/usr/bin/env python3
"""Serve the desk card locally and share the terminal tool's decision logic."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from mimetypes import guess_type

from desk import ROOT, load_notes, minutes, order_notes, recommend

START = ROOT / "data/starting.json"
HANDOFF = ROOT / "data/minute-40.json"
ASSETS = {
    "/": "index.html",
    "/desk.css": "desk.css",
    "/desk.js": "desk.js",
    "/vendor/gsap.min.js": "vendor/gsap.min.js",
    "/vendor/figtree.woff2": "vendor/figtree.woff2",
    "/vendor/newsreader.woff2": "vendor/newsreader.woff2",
}


class DeskHandler(BaseHTTPRequestHandler):
    def respond(self, status, mime, body):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def respond_json(self, status, value):
        self.respond(status, "application/json", json.dumps(value).encode())

    def desk(self, updates=(), now="13:55"):
        notes = order_notes([*load_notes(START), *updates])
        result = recommend(notes, now)
        result["notes"] = [note for note in notes if minutes(note["at"]) <= minutes(now)]
        result["demo_available"] = HANDOFF.exists()
        self.respond_json(200, result)

    def do_GET(self):
        if self.path == "/api/desk":
            self.desk()
        elif self.path == "/minute-40.json" and HANDOFF.is_file():
            self.respond(200, "application/json", HANDOFF.read_bytes())
        elif self.path in ASSETS:
            path = ROOT / "web" / ASSETS[self.path]
            self.respond(200, guess_type(path)[0], path.read_bytes())
        else:
            self.respond_json(404, {"error": "That page was not found."})

    def do_POST(self):
        if self.path != "/api/desk":
            self.respond_json(404, {"error": "That page was not found."})
            return
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 65_536 or self.headers.get_content_type() != "application/json":
                raise ValueError("Choose a JSON handoff smaller than 64 KB.")
            update = json.loads(self.rfile.read(size))
            notes = update["notes"]
            self.desk(notes if isinstance(notes, list) else [notes], update["at"])
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            self.respond_json(400, {"error": f"Check the handoff’s JSON fields. {exc}"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8731)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), DeskHandler) as server:
        print(f"Open http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
