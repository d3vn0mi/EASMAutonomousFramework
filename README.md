# RAVEN EASM Platform

External Attack Surface Management platform built with Django, deployed at `easm.ravensec.eu`.

## Architecture

- **Web**: Django 5.1 + Daphne (ASGI) + Tailwind CSS
- **Database**: PostgreSQL 16
- **Task Queue**: Celery + Redis
- **Real-time**: Django Channels (WebSocket for scan progress)
- **Scanner**: Dedicated container with 20+ recon tools (amass, subfinder, nmap, nuclei, etc.)
- **AI Correlation**: Configurable — Claude, OpenAI, or Ollama (local)
- **Proxy**: Nginx with Let's Encrypt SSL

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your secrets

# 2. Build and start all services
docker compose up -d --build

# 3. Run migrations and create admin user
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# 4. (Production) Obtain SSL certificate
docker compose exec nginx certbot --nginx -d easm.ravensec.eu
```

## Services (7 containers)

| Service | Purpose |
|---------|---------|
| `nginx` | Reverse proxy, SSL termination, static files |
| `web` | Django application (HTTP + WebSocket) |
| `db` | PostgreSQL database |
| `redis` | Celery broker, Channels layer, cache |
| `celery_worker` | General tasks (reports, correlation, documents) |
| `celery_beat` | Periodic task scheduler |
| `scanner` | Celery worker with all recon tools installed |

## User Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access: user management, system config, all operations |
| **Project Manager** | Client/engagement management, assign testers, approve reports |
| **Tester** | Execute scans, add findings, view assigned engagements |

## EASM Workflow

1. **Scope** — Define targets: domains, IPs, CIDRs, emails, names
2. **Scan** — Automated tool workflows per scope type (tier-dependent depth)
3. **Correlate** — AI-powered analysis identifies attack chains and patterns
4. **Report** — Generate executive and technical reports from DOCX templates

## Assessment Tiers

- **Bronze**: Automated discovery (subfinder, amass, httpx, nmap top-1000, nuclei)
- **Silver**: + theHarvester, full port scan, testssl, wafw00f, manual validation
- **Gold**: + all Silver tools with extended options, attack chain construction

## Project Structure

```
raven/                          # Django project root
├── apps/
│   ├── accounts/               # Auth, RBAC, audit log
│   ├── clients/                # Client, Contact, Asset management
│   ├── engagements/            # Engagement lifecycle, scope, checklists
│   ├── scanning/               # Scan orchestration, tool runners, WebSocket
│   ├── findings/               # Finding CRUD, escalation, remediation
│   ├── correlation/            # AI engine abstraction (Claude/OpenAI/Ollama)
│   ├── reports/                # Report generation from DOCX templates
│   ├── dashboard/              # Overview statistics
│   └── api/                    # REST API (DRF)
├── core/                       # Shared mixins, validators, middleware
├── templates/                  # Tailwind CSS templates (EN/GR i18n)
└── documentation/              # DOCX/XLSX/PPTX templates (EN + GR)
```

## API

REST API available at `/api/v1/` — session-authenticated, supports CRUD for clients, engagements, findings, and read-only access to scans and reports.

## Bilingual Support

All UI and reports support English and Greek (Ελληνικά) via Django i18n. Report templates are available in both languages. Language is configurable per-engagement and per-user.
