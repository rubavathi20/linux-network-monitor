
# Linux Network Monitoring Dashboard

A Linux-based network monitoring and troubleshooting platform built with Python and Flask. It provides a web dashboard for viewing network health, system metrics, monitoring reports, and troubleshooting results.

## Features

- Network connectivity monitoring
- DNS resolution checks
- HTTPS availability checks
- System resource monitoring
- Listening TCP port checks
- Health-check API
- Monitoring reports and alerts
- Automated troubleshooting
- Scheduled monitoring using cron
- Automated tests with pytest
- GitHub Actions CI workflow

## Technology Stack

- Linux / Ubuntu
- Python
- Flask
- Bash
- pytest
- Git and GitHub
- GitHub Actions
- Cron
- Docker (containerization verification pending)

## Project Structure

```text
linux-network-monitor/
├── app/
│   ├── app.py
│   ├── monitor.py
│   ├── alerts.py
│   ├── troubleshoot.py
│   ├── requirements.txt
│   ├── templates/
│   └── static/
├── scripts/
├── reports/
├── logs/
├── tests/
│   └── test_app.py
├── .github/
│   └── workflows/
├── Dockerfile
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/rubavathi20/linux-network-monitor.git
cd linux-network-monitor
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r app/requirements.txt
```

## Run the Dashboard

```bash
python app/app.py
```

Open the dashboard at:

http://localhost:5000

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Dashboard |
| `/health` | GET | Application health |
| `/api/report` | GET | Current monitoring report |
| `/api/refresh` | POST | Refresh monitoring report |
| `/api/troubleshoot` | POST | Run troubleshooting |

## Run Automated Tests

```bash
pytest -v
```

The current test suite contains six Flask application tests. GitHub Actions is configured to run automated checks.

## Future Improvements

- Verify Docker image build and container execution
- Add more unit tests for monitoring functions
- Improve monitoring visualizations and alert handling

## Author

Rubavathi

GitHub: https://github.com/rubavathi20

