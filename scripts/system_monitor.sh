
#!/bin/bash

echo "=================================="
echo "     LINUX SYSTEM MONITOR"
echo "=================================="
echo "Date: $(date)"
echo

echo "---- CPU Load ----"
uptime

echo
echo "---- Memory Usage ----"
free -h

echo
echo "---- Disk Usage ----"
df -h /

echo
echo "---- System Uptime ----"
uptime -p

echo
echo "---- Failed System Services ----"
systemctl --failed --no-pager || true

