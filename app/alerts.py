
#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_FILE = BASE_DIR / "reports" / "monitoring_report.json"
ALERT_FILE = BASE_DIR / "reports" / "alerts.log"

CHECKS = {
    "Connectivity": ("network", "connectivity"),
    "DNS": ("network", "dns"),
    "HTTPS": ("network", "https"),
    "Listening TCP ports": ("network", "listening_tcp_ports"),
}


def main():
    if not REPORT_FILE.exists():
        print(f"ERROR: Monitoring report not found: {REPORT_FILE}")
        return 1

    try:
        with REPORT_FILE.open("r", encoding="utf-8") as file:
            report = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: Cannot read monitoring report: {error}")
        return 1

    problems = []

    for check_name, path in CHECKS.items():
        result = report

        for key in path:
            result = result.get(key, {}) if isinstance(result, dict) else {}

        if not isinstance(result, dict):
            problems.append(f"{check_name}: result is missing")
            continue

        status = str(result.get("status", "unknown")).lower()

        if status != "healthy":
            details = (
                result.get("message")
                or result.get("error")
                or result.get("description")
                or "Check is not healthy"
            )
            problems.append(
                f"{check_name}: {status.upper()} - {details}"
            )

    timestamp = datetime.now(timezone.utc).isoformat()

    if problems:
        lines = [
            f"[{timestamp}] ALERT: Network monitoring detected problems:",
            *[f"  - {problem}" for problem in problems],
            "",
        ]
        message = "\n".join(lines)
        print(message, end="")

        with ALERT_FILE.open("a", encoding="utf-8") as file:
            file.write(message)

        return 1

    print(f"[{timestamp}] OK: All network checks are healthy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

