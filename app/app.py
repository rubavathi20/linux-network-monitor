
import json
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_FILE = BASE_DIR / "reports" / "monitoring_report.json"
TROUBLESHOOT_SCRIPT = BASE_DIR / "scripts" / "troubleshoot.sh"

app = Flask(__name__)


def read_report():
    if not REPORT_FILE.exists():
        return {
            "overall_status": "unknown",
            "system": {},
            "network": {},
            "alerts": ["No monitoring report found."]
        }

    try:
        with REPORT_FILE.open(encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {
            "overall_status": "error",
            "system": {},
            "network": {},
            "alerts": ["Report could not be read."]
        }


@app.route("/")
def dashboard():
    return render_template("index.html", report=read_report())


@app.route("/api/report")
def api_report():
    return jsonify(read_report())


@app.route("/api/refresh", methods=["POST"])
def refresh_report():
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "app" / "monitor.py")],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=str(BASE_DIR)
        )

        if result.returncode != 0:
            return jsonify({
                "error": result.stderr[-2000:] or "Monitoring failed."
            }), 500

        return jsonify(read_report())

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Monitoring timed out."}), 504
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/troubleshoot", methods=["POST"])
def troubleshoot():
    try:
        result = subprocess.run(
            ["/usr/bin/bash", str(TROUBLESHOOT_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BASE_DIR)
        )

        report_files = sorted(
            (BASE_DIR / "reports").glob("troubleshooting_*.txt"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        report_text = ""
        if report_files:
            report_text = report_files[0].read_text(
                encoding="utf-8", errors="replace"
            )

        output = report_text or result.stdout or result.stderr

        return jsonify({
            "success": result.returncode == 0,
            "output": output,
            "error": result.stderr[-2000:] if result.returncode else ""
        }), 200 if result.returncode == 0 else 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Troubleshooting timed out."}), 504
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "Linux Network Monitor"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

