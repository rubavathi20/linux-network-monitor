# Linux Network Monitoring Dashboard

A Python and Flask-based network monitoring tool that checks network connectivity, DNS resolution, HTTPS availability, system resource usage, and listening TCP ports on Linux.

## Features

- Network connectivity monitoring
- DNS resolution checks
- HTTPS endpoint monitoring
- CPU, memory, disk, and uptime metrics
- Listening TCP port inspection
- Web dashboard built with Flask
- JSON monitoring reports
- Automated alert detection
- Cron-based scheduled monitoring

## Technologies

- Python
- Flask
- Linux / Ubuntu
- Bash
- Cron
- Git and GitHub
- HTML, CSS, and JavaScript

## Run locally

```bash
git clone https://github.com/rubavathi20/linux-network-monitor.git
cd linux-network-monitor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python app/app.py
```

Open `http://localhost:5000` in your browser.

## Run a monitoring check

```bash
python app/monitor.py
```

## Run alert checks

```bash
python app/alerts.py
```

## Project purpose

This project demonstrates Linux administration, network troubleshooting, monitoring automation, Python scripting, and basic operational alerting skills relevant to DevOps and support engineering.
