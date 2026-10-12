
import json
import platform
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import psutil


BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_FILE = REPORT_DIR / "monitoring_report.json"


def check_connectivity():
    """Check external IP connectivity and packet loss."""
    ping = shutil.which("ping")

    if not ping:
        return {"status": "error", "message": "ping not installed"}

    try:
        result = subprocess.run(
            [ping, "-c", "4", "-W", "2", "1.1.1.1"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr
        match = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss", output)
        loss = float(match.group(1)) if match else None

        return {
            "status": "healthy" if result.returncode == 0 else "failed",
            "host": "1.1.1.1",
            "packet_loss_percent": loss,
            "message": "Ping completed" if result.returncode == 0
                       else "No successful ping response"
        }

    except (subprocess.SubprocessError, OSError) as exc:
        return {"status": "error", "message": str(exc)}


def check_dns():
    """Check system DNS resolution."""
    hostname = "google.com"

    try:
        results = socket.getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM
        )
        addresses = sorted({item[4][0] for item in results})

        return {
            "status": "healthy",
            "hostname": hostname,
            "resolved_ips": addresses
        }

    except socket.gaierror as exc:
        return {
            "status": "failed",
            "hostname": hostname,
            "message": str(exc)
        }


def check_https():
    """Test an external HTTPS endpoint."""
    url = "https://example.com"

    try:
        request = Request(
            url,
            headers={"User-Agent": "LinuxNetworkMonitor/1.0"}
        )

        with urlopen(request, timeout=5) as response:
            return {
                "status": "healthy",
                "url": url,
                "http_status": response.status
            }

    except HTTPError as exc:
        return {
            "status": "degraded",
            "url": url,
            "http_status": exc.code,
            "message": "HTTP error response received"
        }

    except (URLError, TimeoutError, OSError) as exc:
        return {
            "status": "failed",
            "url": url,
            "message": str(exc)
        }


def check_listening_ports():
    """Collect local TCP listening ports."""
    ss = shutil.which("ss")

    if not ss:
        return {
            "status": "error",
            "ports": [],
            "message": "ss command not installed"
        }

    try:
        result = subprocess.run(
            [ss, "-lntH"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )

        ports = []

        for line in result.stdout.splitlines():
            fields = line.split()

            if len(fields) < 4:
                continue

            address = fields[3]
            try:
                port = int(address.rsplit(":", 1)[1])
            except (ValueError, IndexError):
                continue

            ports.append({"address": address, "port": port})

        return {
            "status": "healthy",
            "count": len(ports),
            "ports": ports
        }

    except (subprocess.SubprocessError, OSError) as exc:
        return {
            "status": "error",
            "ports": [],
            "message": str(exc)
        }


def collect_metrics():
    """Collect system metrics and network health."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = max(0, int(time.time() - psutil.boot_time()))

    system = {
        "hostname": socket.gethostname(),
        "operating_system": platform.platform(),
        "cpu_usage_percent": cpu,
        "memory_usage_percent": memory.percent,
        "memory_total_mb": round(memory.total / (1024 ** 2), 2),
        "memory_available_mb": round(memory.available / (1024 ** 2), 2),
        "disk_usage_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "uptime_seconds": uptime
    }

    network = {
        "connectivity": check_connectivity(),
        "dns": check_dns(),
        "https": check_https(),
        "listening_tcp_ports": check_listening_ports()
    }

    alerts = []

    if cpu >= 90:
        alerts.append("High CPU usage")

    if memory.percent >= 90:
        alerts.append("High memory usage")

    if disk.percent >= 90:
        alerts.append("High disk usage")

    for name in ("connectivity", "dns", "https"):
        result = network[name]
        if result["status"] != "healthy":
            alerts.append(
                f"{name.upper()} check: "
                f"{result.get('message', result['status'])}"
            )

    if (
        network["connectivity"]["status"] == "failed"
        and network["dns"]["status"] == "failed"
    ):
        overall = "critical"
    elif alerts:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "system": system,
        "network": network,
        "alerts": alerts
    }


def save_report(report):
    """Save the latest metrics as JSON."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = REPORT_FILE.with_suffix(".tmp")

    temp_file.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )
    temp_file.replace(REPORT_FILE)


if __name__ == "__main__":
    print("Starting Linux Network Monitoring Engine...")

    report = collect_metrics()
    save_report(report)

    print("Overall status:", report["overall_status"])
    print("CPU usage:", report["system"]["cpu_usage_percent"], "%")
    print("Memory usage:", report["system"]["memory_usage_percent"], "%")
    print("Disk usage:", report["system"]["disk_usage_percent"], "%")
    print("Connectivity:", report["network"]["connectivity"]["status"])
    print("DNS:", report["network"]["dns"]["status"])
    print("HTTPS:", report["network"]["https"]["status"])
    print("Alerts:", report["alerts"])
    print("Report saved to:", REPORT_FILE)

