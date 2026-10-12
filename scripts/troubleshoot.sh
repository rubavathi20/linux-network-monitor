
#!/usr/bin/env bash

set -u

PROJECT_DIR="$HOME/linux-network-monitor"
REPORT_DIR="$PROJECT_DIR/reports"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/troubleshooting_${TIMESTAMP}.txt"
LOG_FILE="$LOG_DIR/troubleshooting.log"

exec > >(tee -a "$REPORT_FILE" "$LOG_FILE") 2>&1

echo "======================================"
echo " Automated Network Troubleshooting"
echo "======================================"
echo "Time: $(date)"
echo

check_result() {
    local name="$1"
    shift

    echo "Checking: $name"

    if "$@"; then
        echo "RESULT: PASS - $name"
    else
        echo "RESULT: FAIL - $name"
    fi

    echo
}

echo "1. Network interface addresses"
if ip -o -4 addr show up scope global; then
    echo "RESULT: PASS - Network interface detected"
else
    echo "RESULT: FAIL - No active IPv4 interface detected"
fi
echo

echo "2. Internet connectivity"
check_result "Internet connectivity (1.1.1.1)" \
    ping -c 2 -W 3 1.1.1.1

echo "3. DNS resolution"
check_result "DNS resolution (google.com)" \
    getent ahosts google.com

echo "4. HTTPS connectivity"
check_result "HTTPS connectivity (example.com)" \
    curl -fsSI --connect-timeout 5 --max-time 10 \
    https://example.com

echo "5. Listening TCP ports"
if command -v ss >/dev/null 2>&1; then
    ss -lnt
else
    echo "ss command is unavailable"
fi
echo

echo "6. Troubleshooting summary"
echo "Report saved to: $REPORT_FILE"
echo "Log saved to: $LOG_FILE"
echo "Completed: $(date)"


