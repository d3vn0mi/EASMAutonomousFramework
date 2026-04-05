# RAVEN EASM Platform - Deployment, Configuration & Testing Guide

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Server Preparation](#2-server-preparation)
3. [Clone & Configure](#3-clone--configure)
4. [SSL Certificate Setup](#4-ssl-certificate-setup)
5. [Build & Launch Containers](#5-build--launch-containers)
6. [Database Initialization](#6-database-initialization)
7. [Create Admin User](#7-create-admin-user)
8. [Configure API Keys](#8-configure-api-keys)
9. [Upload Document Templates](#9-upload-document-templates)
10. [Verify All Services](#10-verify-all-services)
11. [Functional Testing Walkthrough](#11-functional-testing-walkthrough)
12. [Tool Verification](#12-tool-verification)
13. [Troubleshooting](#13-troubleshooting)
14. [Maintenance & Updates](#14-maintenance--updates)

---

## 1. Prerequisites

### Server Requirements

| Component        | Minimum          | Recommended       |
|-----------------|------------------|-------------------|
| OS              | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS  |
| CPU             | 4 cores          | 8+ cores          |
| RAM             | 8 GB             | 16+ GB            |
| Disk            | 50 GB SSD        | 100+ GB SSD       |
| Network         | Public IP         | Dedicated IP       |

### Software Requirements

```bash
# Docker Engine 24+
# Docker Compose v2+
# Git
# A domain name pointing to the server (easm.ravensec.eu)
```

### Domain DNS

Before starting, ensure your domain has an A record pointing to the server IP:

```
easm.ravensec.eu.  IN  A  <YOUR_SERVER_IP>
```

Verify with:
```bash
dig +short easm.ravensec.eu
```

---

## 2. Server Preparation

### Install Docker & Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add your user to docker group (log out/in after)
sudo usermod -aG docker $USER

# Verify
docker --version
docker compose version
```

### Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Verify
sudo ufw status
```

### Create Project Directory

```bash
sudo mkdir -p /opt/raven
sudo chown $USER:$USER /opt/raven
cd /opt/raven
```

---

## 3. Clone & Configure

### Clone Repository

```bash
cd /opt/raven
git clone <REPOSITORY_URL> .
```

### Create Environment File

```bash
cp .env.example .env
```

### Edit Environment Variables

```bash
nano .env
```

**Critical variables to change:**

```ini
# ── SECURITY (MUST CHANGE) ─────────────────────────────────────────────
DJANGO_SECRET_KEY=<generate-a-64-char-random-string>
POSTGRES_PASSWORD=<strong-database-password>

# ── DOMAIN ──────────────────────────────────────────────────────────────
DJANGO_ALLOWED_HOSTS=easm.ravensec.eu,localhost,127.0.0.1
DOMAIN=easm.ravensec.eu
CERTBOT_EMAIL=admin@ravensec.eu

# ── AI CORRELATION ENGINE ──────────────────────────────────────────────
# Choose: claude, openai, or ollama
CORRELATION_ENGINE=claude
ANTHROPIC_API_KEY=sk-ant-...       # Required if engine=claude
OPENAI_API_KEY=sk-...              # Required if engine=openai
OLLAMA_BASE_URL=http://ollama:11434  # Required if engine=ollama

# ── EXTERNAL TOOL API KEYS (optional but recommended) ──────────────────
SHODAN_API_KEY=                    # For passive infrastructure intel
CENSYS_API_ID=                     # For certificate/host search
CENSYS_API_SECRET=
HIBP_API_KEY=                      # For breach data lookups
GITHUB_API_TOKEN=                  # For GitHub org/repo enumeration
```

**Generate a secure secret key:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Generate a secure database password:**

```bash
openssl rand -base64 32
```

---

## 4. SSL Certificate Setup

### Option A: Let's Encrypt (Production)

SSL certificates are obtained automatically via Certbot. However, Nginx needs to start first with a temporary self-signed cert.

**Step 1: Create temporary self-signed certificate**

```bash
mkdir -p docker/nginx/certbot
sudo mkdir -p /tmp/letsencrypt/live/easm.ravensec.eu

# Generate temporary self-signed cert
sudo openssl req -x509 -nodes -days 1 \
  -newkey rsa:2048 \
  -keyout /tmp/letsencrypt/live/easm.ravensec.eu/privkey.pem \
  -out /tmp/letsencrypt/live/easm.ravensec.eu/fullchain.pem \
  -subj "/CN=easm.ravensec.eu"
```

**Step 2: Start Nginx with temporary cert**

```bash
# Start only nginx and web
docker compose up -d nginx web db redis

# Wait for services to be healthy
docker compose ps
```

**Step 3: Obtain real Let's Encrypt certificate**

```bash
docker compose exec nginx certbot --nginx \
  -d easm.ravensec.eu \
  --non-interactive \
  --agree-tos \
  -m admin@ravensec.eu
```

**Step 4: Set up auto-renewal**

Add to the host's crontab:

```bash
crontab -e
```

Add this line:

```
0 3 * * * docker compose -f /opt/raven/docker-compose.yml exec -T nginx certbot renew --quiet && docker compose -f /opt/raven/docker-compose.yml exec -T nginx nginx -s reload
```

### Option B: Self-Signed (Development/Testing)

```bash
mkdir -p docker/nginx/certs

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout docker/nginx/certs/privkey.pem \
  -out docker/nginx/certs/fullchain.pem \
  -subj "/CN=localhost"
```

Then update `docker/nginx/nginx.conf` to point to these paths and change `server_name` to `localhost`.

---

## 5. Build & Launch Containers

### Build All Images

```bash
docker compose build
```

This builds 3 custom images:
- **web** (~500 MB) - Django + Daphne + WeasyPrint
- **scanner** (~3 GB) - All 40+ recon tools + Celery worker
- **nginx** (~30 MB) - Nginx + Certbot

Expected build time: 10-20 minutes (scanner image is large).

### Start All Services

```bash
docker compose up -d
```

### Verify All Containers Are Running

```bash
docker compose ps
```

Expected output:

```
NAME                SERVICE          STATUS
raven-db-1          db               running (healthy)
raven-redis-1       redis            running (healthy)
raven-web-1         web              running
raven-celery_worker-1  celery_worker  running
raven-celery_beat-1    celery_beat    running
raven-scanner-1     scanner          running
raven-nginx-1       nginx            running
```

All 7 containers must show `running`. The `db` and `redis` containers should show `healthy`.

### Check Logs for Errors

```bash
# All services
docker compose logs --tail=50

# Specific service
docker compose logs web --tail=30
docker compose logs scanner --tail=30
docker compose logs celery_worker --tail=30
```

---

## 6. Database Initialization

### Run Migrations

```bash
docker compose exec web python manage.py migrate
```

Expected output: A series of migration lines ending with `OK` for each app:
- accounts
- clients
- engagements
- scanning
- findings
- correlation
- reports

### Collect Static Files

This should have run during build, but verify:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

---

## 7. Create Admin User

### Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

Enter:
- **Username**: `admin` (or your choice)
- **Email**: `admin@ravensec.eu`
- **Password**: A strong password (12+ chars)

This user will have the `admin` role with full access.

### Create Additional Users (Optional)

Log into the web interface and create users via the Accounts management:

| Role             | Access Level |
|-----------------|-------------|
| `admin`          | Full access: all clients, engagements, users, settings |
| `project_manager` | Manage engagements, assign testers, approve reports |
| `tester`         | Run scans, manage findings, view assigned engagements |

---

## 8. Configure API Keys

### Required for AI Correlation (at least one)

| Engine | Environment Variable | How to Get |
|--------|---------------------|-----------|
| Claude (Anthropic) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| OpenAI | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| Ollama (Local) | `OLLAMA_BASE_URL` | [ollama.com](https://ollama.com) - self-hosted |

### Optional but Recommended

| Service | Variable | Purpose | How to Get |
|---------|----------|---------|-----------|
| Shodan | `SHODAN_API_KEY` | Passive port/service intelligence | [account.shodan.io](https://account.shodan.io) |
| Censys | `CENSYS_API_ID` + `CENSYS_API_SECRET` | Certificate/host search | [censys.io/account/api](https://censys.io/account/api) |
| HIBP | `HIBP_API_KEY` | Breach data for emails/domains | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) |
| GitHub | `GITHUB_API_TOKEN` | Org repo enumeration, code search | GitHub Settings > Developer Settings > Personal Access Tokens |

After updating `.env`, restart the affected services:

```bash
docker compose up -d
```

---

## 9. Upload Document Templates

The platform generates DOCX reports from templates. Place your templates in the `documentation/` directory:

```bash
ls documentation/
```

Expected template naming convention:

```
RAVEN_Report_Bronze.docx
RAVEN_Report_Silver.docx
RAVEN_Report_Gold.docx
RAVEN_Report_Bronze_GR.docx    # Greek version
RAVEN_Report_Silver_GR.docx
RAVEN_Report_Gold_GR.docx
```

Templates use placeholder syntax: `{{CLIENT_NAME}}`, `{{ENGAGEMENT_ID}}`, `{{DATE}}`, etc.

---

## 10. Verify All Services

### 10a. Web Application

Open `https://easm.ravensec.eu` in your browser. You should see the RAVEN login page.

```bash
# Or test from the server
curl -k -I https://localhost
```

Expected: HTTP 302 redirect to `/accounts/login/`

### 10b. Django Admin

Navigate to `https://easm.ravensec.eu/admin/` and log in with your superuser credentials.

### 10c. REST API

```bash
# Should return 403 (unauthenticated)
curl -k https://easm.ravensec.eu/api/clients/

# Authenticate with session
curl -k -c cookies.txt -X POST https://easm.ravensec.eu/accounts/login/ \
  -d "username=admin&password=YOUR_PASSWORD"
curl -k -b cookies.txt https://easm.ravensec.eu/api/clients/
```

### 10d. Database Connectivity

```bash
docker compose exec web python manage.py dbshell
# Should open a psql prompt
\dt    # List tables - should show 20+ tables
\q     # Exit
```

### 10e. Redis Connectivity

```bash
docker compose exec redis redis-cli ping
# Expected: PONG

docker compose exec redis redis-cli info keyspace
```

### 10f. Celery Workers

```bash
# Check default worker
docker compose exec celery_worker celery -A raven inspect active
docker compose exec celery_worker celery -A raven inspect stats

# Check scanner worker
docker compose exec scanner celery -A raven inspect active -d celery@scanner
```

### 10g. Scanner Tools Availability

```bash
docker compose exec scanner bash -c "
  echo '=== Tool Verification ==='
  which subfinder && subfinder -version
  which amass && amass -version
  which nuclei && nuclei -version
  which httpx && httpx -version
  which nmap && nmap --version | head -1
  which masscan && masscan --version 2>&1 | head -1
  which dnsx && dnsx -version
  which feroxbuster && feroxbuster --version
  which trufflehog && trufflehog --version 2>&1 | head -1
  which gitleaks && gitleaks version
  which gowitness && gowitness version 2>&1 || echo 'gowitness installed'
  which whatweb && whatweb --version 2>&1 | head -1
  which wafw00f && wafw00f --version 2>&1 | head -1
  which waybackurls && echo 'waybackurls installed'
  which gau && echo 'gau installed'
  which assetfinder && echo 'assetfinder installed'
  which dnstwist && dnstwist --version 2>&1 | head -1
  which whois && echo 'whois installed'
  which testssl.sh || which testssl && echo 'testssl installed'
  echo '=== SecLists ==='
  ls /opt/seclists/Discovery/Web-Content/ | head -5
  echo '=== Nuclei Templates ==='
  ls ~/nuclei-templates/ | head -5
  echo '=== All tools verified ==='
"
```

### 10h. WebSocket Connectivity

Open the browser developer console on a scan detail page and verify the WebSocket connects:

```
WebSocket connection to 'wss://easm.ravensec.eu/ws/scan/<id>/' established
```

---

## 11. Functional Testing Walkthrough

This is a step-by-step test of the complete engagement lifecycle.

### Step 1: Create a Client

1. Log in as `admin`
2. Navigate to **Clients** > **New Client**
3. Fill in:
   - Name: `Test Company`
   - Industry: `Technology`
   - Website: `https://example.com`
   - Status: Active
4. Click **Save**
5. Add a **Contact**: name, email, phone, role

### Step 2: Add Client Assets

1. Go to the client detail page
2. Click **Add Asset** or use **Bulk Import**
3. Add at least one domain: `example.com`
4. Optionally add: IP addresses, email addresses

### Step 3: Create an Engagement

1. Navigate to **Engagements** > **New Engagement**
2. Fill in:
   - Client: `Test Company`
   - Name: `Q2 2026 EASM Assessment`
   - Tier: **Silver** (recommended for testing)
   - Language: English
   - Start/End dates
3. Click **Save**
4. An engagement ID (e.g., `RAVEN-EASM-2026-001`) is auto-generated

### Step 4: Define Scope

1. On the engagement detail page, go to **Scope**
2. Add scope items:
   - Type: Domain, Value: `example.com`, In Scope: Yes
   - Type: Email, Value: `info@example.com`, In Scope: Yes
3. Or use **Bulk Import** to paste multiple items

### Step 5: Complete Pre-Engagement Checklist

1. Go to **Checklist** tab
2. Check off items as they are completed:
   - Statement of Work signed
   - Rules of Engagement signed
   - Domains confirmed
   - Tier confirmed
   - etc.

### Step 6: Run a Scan

1. Go to **Scans** tab on the engagement
2. Click **Start Scan**
3. Select phase (or let it auto-detect)
4. The scan dispatches to the scanner container

**Monitor progress:**
- The scan detail page shows real-time progress via WebSocket
- Progress bar updates as each tool completes
- Each tool execution is logged with status, output, and timing

**For Silver tier on a domain, the following tools run in order:**
1. Subfinder (subdomain discovery)
2. Amass (subdomain discovery)
3. Assetfinder (subdomain discovery)
4. crt.sh (certificate transparency)
5. WHOIS (domain registration)
6. theHarvester (email/host discovery)
7. HttpX (HTTP probing)
8. Nmap (full port scan)
9. Nuclei (vulnerability scanning)
10. WhatWeb (technology fingerprinting)
11. GoWitness (screenshots)
12. Testssl (SSL/TLS assessment)
13. Wafw00f (WAF detection)
14. WaybackUrls (historical URLs)
15. GAU (historical URLs)
16. Dnstwist (typosquatting)
17. Shodan (passive intelligence)

### Step 7: Review Discovered Assets

1. Go to **Assets** tab on the engagement
2. Review discovered subdomains, IPs, URLs
3. Assets include metadata: technology stacks, WHOIS data, SSL info

### Step 8: Review Findings

1. Go to **Findings** tab
2. Findings are auto-imported from Nuclei, Testssl, email security checks
3. Each finding has:
   - Severity (Critical/High/Medium/Low/Info)
   - CVSS score
   - Description and evidence
   - Recommendation
   - Remediation status tracking
4. You can manually add findings or mark false positives

### Step 9: Run AI Correlation

1. Go to **Correlation** tab
2. Click **Run Correlation**
3. Select engine (Claude/OpenAI/Ollama) or use the default
4. The AI analyzes all findings and assets to produce:
   - **Attack chains**: Multi-step exploitation paths
   - **Patterns**: Recurring issues across the attack surface
   - **Risk priorities**: Findings ranked by exploitability and impact
   - **Executive summary**: Board-ready overview
   - **Remediation plan**: Phased timeline (Gold tier: multi-pass analysis)

### Step 10: Generate Reports

1. Go to **Reports** tab
2. Click **Generate Report**
3. Select:
   - **Report Type**: Executive or Technical
   - **Format**: HTML, PDF, or DOCX

**HTML Report** produces a self-contained dark-theme document with 15 sections:
1. Executive Summary
2. Scope & Methodology
3. Attack Surface Overview
4. Domain & Subdomain Discovery
5. DNS & Infrastructure Analysis
6. Web Application Analysis
7. SSL/TLS Assessment
8. Port & Service Analysis
9. Vulnerability Findings
10. Data Breach Exposure
11. Email Security
12. Attack Chain Analysis
13. Risk Prioritization & Remediation
14. Recommendations
15. Appendices

**PDF Report** renders the same HTML content to PDF via WeasyPrint.

**DOCX Report** uses template-based placeholder replacement.

### Step 11: Review and Deliver

1. Reports go through an approval workflow:
   - Draft -> Generated -> Under Review -> Approved -> Delivered
2. Approved reports can be downloaded and delivered to the client
3. The engagement status progresses: Active -> Reporting -> Review -> Delivered

### Step 12: Remediation Tracking

1. For each finding, track remediation:
   - Open -> In Progress -> Remediated / Accepted Risk / Won't Fix
2. Set remediation deadlines
3. Schedule retests to verify fixes

---

## 12. Tool Verification

### Quick Scan Test

Run a quick scan against a safe test domain to verify end-to-end:

```bash
# Enter the scanner container
docker compose exec scanner bash

# Test individual tools
subfinder -d example.com -silent | head -5
echo "example.com" | httpx -silent -status-code
nmap -sT -T4 --top-ports 10 example.com
whois example.com | head -20
```

### Verify API-Based Tools

```bash
# Inside scanner container or web container
docker compose exec web python -c "
from django.conf import settings
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'raven.settings.production'
import django; django.setup()

print('Shodan API key:', 'SET' if settings.SHODAN_API_KEY else 'NOT SET')
print('HIBP API key:', 'SET' if settings.HIBP_API_KEY else 'NOT SET')
print('GitHub token:', 'SET' if settings.GITHUB_API_TOKEN else 'NOT SET')
print('Anthropic key:', 'SET' if settings.ANTHROPIC_API_KEY else 'NOT SET')
print('OpenAI key:', 'SET' if settings.OPENAI_API_KEY else 'NOT SET')
print('Correlation engine:', settings.CORRELATION_ENGINE)
"
```

### Verify Celery Task Routing

```bash
docker compose exec celery_worker celery -A raven inspect registered
```

Should list tasks including:
- `apps.scanning.tasks.run_scan_workflow`
- `apps.scanning.tasks.run_tool_execution`
- `apps.correlation.tasks.run_correlation`
- `apps.reports.tasks.generate_report`
- `apps.engagements.tasks.generate_document`

---

## 13. Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs <service> --tail=100

# Common issues:
# - db: POSTGRES_PASSWORD not set -> set in .env
# - web: module import error -> rebuild: docker compose build web
# - scanner: build failed -> check network, retry build
```

### Database Connection Refused

```bash
# Check db is healthy
docker compose ps db

# Check credentials match
docker compose exec db psql -U raven -d raven_easm -c "SELECT 1;"

# Reset if needed
docker compose down -v  # WARNING: destroys all data
docker compose up -d
docker compose exec web python manage.py migrate
```

### Migrations Fail

```bash
# Check current migration state
docker compose exec web python manage.py showmigrations

# If migrations are inconsistent, try:
docker compose exec web python manage.py migrate --run-syncdb

# For a fresh start (WARNING: destroys data):
docker compose exec web python manage.py flush --noinput
docker compose exec web python manage.py migrate
```

### Scanner Tools Not Found

```bash
# Rebuild scanner image
docker compose build scanner --no-cache

# Verify tool installation
docker compose exec scanner which subfinder amass nuclei httpx
```

### SSL Certificate Issues

```bash
# Check cert status
docker compose exec nginx certbot certificates

# Force renewal
docker compose exec nginx certbot renew --force-renewal

# Restart nginx
docker compose restart nginx
```

### Celery Tasks Not Processing

```bash
# Check worker status
docker compose exec celery_worker celery -A raven inspect active

# Check queue lengths
docker compose exec redis redis-cli LLEN default
docker compose exec redis redis-cli LLEN scanning

# Restart workers
docker compose restart celery_worker scanner

# Check for errors
docker compose logs celery_worker --tail=50
docker compose logs scanner --tail=50
```

### WebSocket Not Connecting

```bash
# Check ASGI is running
docker compose logs web | grep -i "daphne\|websocket"

# Verify Nginx WebSocket config
docker compose exec nginx cat /etc/nginx/nginx.conf | grep -A5 "ws/"

# Check Channels layer
docker compose exec web python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='raven.settings.production'
import django; django.setup()
from channels.layers import get_channel_layer
layer = get_channel_layer()
print('Channel layer:', type(layer).__name__)
"
```

### Reports Generation Fails

```bash
# Check WeasyPrint dependencies
docker compose exec web python -c "from weasyprint import HTML; print('WeasyPrint OK')"

# Check template directory
docker compose exec web ls /templates/

# Check celery worker logs
docker compose logs celery_worker --tail=50 | grep -i "report\|error"
```

---

## 14. Maintenance & Updates

### Pulling Updates

```bash
cd /opt/raven
git pull origin main

# Rebuild images
docker compose build

# Apply new migrations
docker compose exec web python manage.py migrate

# Restart
docker compose up -d
```

### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U raven raven_easm > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup_YYYYMMDD_HHMMSS.sql | docker compose exec -T db psql -U raven raven_easm
```

### Log Management

```bash
# View logs
docker compose logs --tail=100 -f

# Docker log rotation (add to /etc/docker/daemon.json):
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Update Nuclei Templates

```bash
docker compose exec scanner nuclei -update-templates
```

### Update Scanner Tools

```bash
# Rebuild scanner with latest tool versions
docker compose build scanner --no-cache
docker compose up -d scanner
```

### Monitor Disk Usage

```bash
# Check Docker volumes
docker system df

# Check specific volumes
docker volume ls
docker volume inspect raven_postgres_data

# Clean unused images/containers
docker system prune -f
```

---

## Architecture Reference

```
                  Internet
                     |
              [80/443 - Nginx]
                /          \
          [Static]    [Proxy -> :8000]
                          |
                    [Daphne ASGI]
                    /     |     \
               [HTTP] [WebSocket] [REST API]
                          |
                    [Django App]
                   /      |      \
          [PostgreSQL] [Redis]  [Celery]
                                /     \
                    [default queue] [scanning queue]
                         |              |
                  [celery_worker]   [scanner]
                  (reports,         (40+ recon
                   correlation,      tools)
                   documents)
```

### Service Ports (Internal)

| Service     | Port | Protocol |
|-------------|------|----------|
| PostgreSQL  | 5432 | TCP      |
| Redis       | 6379 | TCP      |
| Django/Daphne | 8000 | HTTP/WS |
| Nginx       | 80, 443 | HTTP/HTTPS |

### Docker Volumes

| Volume            | Purpose                    |
|-------------------|----------------------------|
| postgres_data     | Database persistence       |
| redis_data        | Redis persistence          |
| media_volume      | Uploaded files, reports, scan output |
| static_volume     | Django collected static files |
| letsencrypt_data  | SSL certificates           |

### Celery Task Routing

| Task Pattern                    | Queue      | Worker          |
|--------------------------------|------------|-----------------|
| `apps.scanning.tasks.*`        | `scanning` | scanner         |
| `apps.correlation.tasks.*`     | `default`  | celery_worker   |
| `apps.reports.tasks.*`         | `default`  | celery_worker   |
| `apps.engagements.tasks.*`     | `default`  | celery_worker   |
