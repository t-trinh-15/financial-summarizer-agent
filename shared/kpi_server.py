"""
shared/kpi_server.py
Lightweight HTTP server that serves KPI data to the team dashboard.
Run in a separate terminal: .venv/bin/python shared/kpi_server.py
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from http.server import HTTPServer, BaseHTTPRequestHandler
from shared.storage import compute_kpis, DB_PATH


def get_recent_interactions(limit=20):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT
                i.merchant,
                i.amount,
                i.currency,
                i.tx_type,
                i.confidence,
                i.timestamp,
                f.accepted AS feedback
            FROM interactions i
            LEFT JOIN feedback f ON f.interaction_id = i.id
            ORDER BY i.timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


class KPIHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/kpis":
            self._send_json(compute_kpis())
        elif self.path.startswith("/interactions"):
            self._send_json(get_recent_interactions())
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):
        pass  # silence request logs


if __name__ == "__main__":
    port = 8765
    print(f"KPI server running at http://localhost:{port}")
    print("Open dashboard/kpi_dashboard.html in your browser.")
    print("Press Ctrl+C to stop.\n")
    HTTPServer(("localhost", port), KPIHandler).serve_forever()