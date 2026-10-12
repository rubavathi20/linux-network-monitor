
#!/bin/bash

# Linux Network Diagnostics
# Project: Linux Network Monitoring & Automated Troubleshooting System

echo "=========================================="
echo "       LINUX NETWORK DIAGNOSTICS"
echo "=========================================="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo

# 1. Check IP connectivity
echo "---- 1. IP Connectivity ----"

if ping -c 4 -W 2 1.1.1.1; then
    echo "STATUS: IP connectivity check passed"
else
    echo "STATUS: IP connectivity check failed"
    echo "Possible cause: Network issue or ICMP blocked"
fi

echo

# 2. Check DNS resolution
echo "---- 2. DNS Resolution ----"

if dig +time=2 +tries=1 +short google.com | grep -qE '^[0-9]+\.'; then
    echo "STATUS: DNS resolution successful"
    dig +time=2 +tries=1 +short google.com
else
    echo "STATUS: DNS resolution failed"
    echo "Check DNS configuration and network access"
fi

echo

# 3. Check packet loss
echo "---- 3. Packet Loss ----"

PING_OUTPUT=$(ping -c 4 -W 2 1.1.1.1 2>&1)
echo "$PING_OUTPUT" | grep -E 'packet loss|packets transmitted' \
    || echo "No packet statistics available"

echo

# 4. Show listening TCP and UDP ports
echo "---- 4. Listening Network Ports ----"

ss -tuln

echo

# 5. Check common service ports
echo "---- 5. Common Service Port Checks ----"

for port in 22 80 443 5000; do
    if ss -lntH | awk '{print $4}' | grep -Eq ":${port}$"; then
        echo "Port $port: LISTENING"
    else
        echo "Port $port: NOT LISTENING"
    fi
done

echo
echo "=========================================="
echo "       DIAGNOSTICS COMPLETED"
echo "=========================================="

