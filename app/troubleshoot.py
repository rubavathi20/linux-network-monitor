
#!/usr/bin/env python3

import socket
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_command(command, timeout=5):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"


def check_connectivity(host="1.1.1.1"):
    code, output, error = run_command(
        ["ping", "-c", "2", "-W", "2", host],
        timeout=6,
    )

    if code == 0:
        return "HEALTHY", f"Ping to {host} succeeded."

    return "UNHEALTHY", error or output or f"Ping to {host} failed."


def check_dns(host="google.com"):
    try:
        addresses = sorted({
            result[4][0]
            for result in socket.getaddrinfo(host, None)
        })
        return "HEALTHY", f"{host} resolved to: {', '.join(addresses)}"
    except socket.gaierror as error:
        return "UNHEALTHY", f"DNS resolution failed: {error}"


def check_https(url="https://example.com"):
    try:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "LinuxNetworkMonitor/1.0"},
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            return "HEALTHY", f"HTTPS reachable; HTTP {response.status}"

    except urllib.error.HTTPError as error:
        # An HTTP response still proves that the endpoint was reachable.
        return "HEALTHY", f"HTTPS reachable; HTTP {error.code}"

    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return "UNHEALTHY", f"HTTPS check failed: {error}"


def main():
    checks = [
        ("Connectivity", check_connectivity),
        ("DNS", check_dns),
        ("HTTPS", check_https),
    ]

    print("Linux Network Troubleshooting Report")
    print(f"Time (UTC): {datetime.now(timezone.utc).isoformat()}")
    print("-" * 55)

    failed = 0

    for name, check in checks:
        try:
            status, details = check()
        except Exception as error:
            status, details = "ERROR", str(error)

        print(f"{name}: {status}")
        print(f"  {details}")

        if status != "HEALTHY":
            failed += 1

    print("-" * 55)
    print(f"Checks failed: {failed}/{len(checks)}")

    return 1 if failed else 0



if __name__ == "__main__":
    import contextlib
    import sys

    log_file = BASE_DIR / "reports" / "troubleshooting.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    class Tee:
        """Write output to both the terminal and a log file."""

        def __init__(self, *streams):
            self.streams = streams

        def write(self, message):
            for stream in self.streams:
                stream.write(message)
                stream.flush()

        def flush(self):
            for stream in self.streams:
                stream.flush()

    with log_file.open("a", encoding="utf-8") as logfile:
        with contextlib.redirect_stdout(Tee(sys.stdout, logfile)):
            exit_code = main()

    raise SystemExit(exit_code)

