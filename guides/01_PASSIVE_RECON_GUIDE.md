# RAVEN EASM - Passive Reconnaissance Guide

## Overview

This guide covers **passive-only** information gathering techniques. Passive recon collects data from public sources, APIs, and databases **without directly touching** the target infrastructure. No packets are sent to target systems.

**Use this when**: You have authorization to research the target but NOT to actively scan their systems, or during the initial intelligence-gathering phase before active engagement.

---

## Prerequisites

### Required Inputs

| Input | Example | Required? |
|-------|---------|-----------|
| Target domains | `example.com`, `corp.example.com` | At least one |
| Target IPs/CIDRs | `203.0.113.0/24`, `198.51.100.42` | Optional |
| Email addresses | `admin@example.com` | Optional |
| GitHub org name | `example-corp` | Optional |
| Git repository URLs | `https://github.com/example-corp/app` | Optional |

### API Keys (Optional but Recommended)

| Service | How to Get | What It Unlocks |
|---------|-----------|-----------------|
| Shodan | [account.shodan.io](https://account.shodan.io) | Port/service/banner data for IPs |
| HIBP | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) | Breach data for emails/domains |
| GitHub | GitHub > Settings > Developer Settings > PAT | Higher API rate limits, private org visibility |

### Tool Installation

All tools below are pre-installed in the RAVEN scanner container. To use them manually:

```bash
docker compose exec scanner bash
```

Or install individually on your workstation (Kali/Debian):
```bash
# Go tools
go install github.com/tomnomnom/waybackurls@latest
go install github.com/lc/gau/v2/cmd/gau@latest

# Python tools
pip install shodan theHarvester dnstwist

# System tools
apt install whois dnsutils
```

---

## Phase 1: Domain Intelligence

> **Input needed**: One or more target domain names

### Step 1.1 - WHOIS Lookup

Retrieve domain registration data: registrar, creation/expiry dates, nameservers, registrant info.

```bash
whois example.com
```

**What to record**:
- Registrar name
- Registration/expiry dates
- Nameservers (these reveal hosting provider)
- Registrant organization, email (if not redacted)
- Related domains under the same registrant

**Tip**: If WHOIS privacy is enabled, note the privacy service — sometimes the registrant org leaks in other fields.

---

### Step 1.2 - Certificate Transparency (crt.sh)

Query public certificate transparency logs to discover subdomains that have had SSL certificates issued.

```bash
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u
```

**What to record**:
- All discovered subdomains
- Wildcard patterns (`*.example.com`)
- Internal-looking names (`staging.example.com`, `vpn.example.com`, `dev-api.example.com`)

---

### Step 1.3 - Passive Subdomain Enumeration (Amass)

Amass queries multiple passive sources (DNS datasets, certificate logs, web archives).

```bash
amass enum -passive -d example.com
```

> **Note**: Use `-passive` flag only. Without it, Amass performs active DNS brute-forcing.

**What to record**:
- All discovered subdomains (compare with crt.sh results)
- Count of unique subdomains found

---

### Step 1.4 - Historical URL Discovery (Wayback Machine)

Retrieve URLs that have been archived by the Wayback Machine and other web crawlers.

```bash
echo "example.com" | waybackurls | sort -u > wayback_urls.txt
```

```bash
gau example.com | sort -u > gau_urls.txt
```

**What to record**:
- Old endpoints that may still be live (`/admin`, `/api/v1`, `/backup`)
- File paths revealing technology stack (`.php`, `.aspx`, `.jsp`)
- API endpoints and parameters
- Leaked paths to internal resources
- Config files (`.env`, `.git/config`, `web.config`)

**Tip**: Filter for interesting patterns:
```bash
cat wayback_urls.txt gau_urls.txt | sort -u | grep -iE '\.(env|config|xml|json|sql|bak|old|zip|tar|gz)$'
cat wayback_urls.txt gau_urls.txt | sort -u | grep -iE '(admin|login|dashboard|api|internal|staging|dev)'
```

---

### Step 1.5 - Typosquatting Detection (dnstwist)

Identify domains that are visually similar to the target (phishing risk).

```bash
dnstwist --format json example.com
```

**What to record**:
- Registered lookalike domains (these could be used for phishing)
- Domains resolving to IP addresses (actively being used)
- Domains with MX records (set up to receive email)

---

### Step 1.6 - OSINT Harvesting (theHarvester)

Gather emails, names, subdomains, and IPs from multiple public search engines and databases.

```bash
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,otx,rapiddns,urlscan
```

**What to record**:
- Email addresses (useful for phishing scope, breach checks, credential stuffing)
- Employee names
- Additional subdomains not found by other tools
- IP addresses associated with the domain

---

## Phase 2: IP & Infrastructure Intelligence

> **Input needed**: IP addresses or CIDR ranges (from WHOIS, DNS resolution, or provided scope)

### Step 2.1 - Shodan Lookup

> **Requires**: `SHODAN_API_KEY` environment variable

Query Shodan for banners, open ports, services, and technologies — all collected passively by Shodan's crawlers.

**For a single IP:**
```bash
shodan host 198.51.100.42
```

**For a domain (find associated IPs):**
```bash
shodan search hostname:example.com
```

**Python alternative (more detail):**
```python
import shodan
api = shodan.Shodan("YOUR_API_KEY")

# Single IP
result = api.host("198.51.100.42")
for item in result.get("data", []):
    print(f"Port {item['port']}: {item.get('product', 'unknown')} {item.get('version', '')}")
    print(f"  Banner: {item.get('data', '')[:200]}")

# Domain search
for result in api.search_cursor(f"hostname:example.com"):
    print(f"{result['ip_str']}:{result['port']} - {result.get('product', '')}")
```

**What to record**:
- Open ports and services (without actively scanning)
- Software versions and banners
- SSL certificate details
- Known vulnerabilities (CVEs) associated with detected versions
- Cloud provider / hosting information
- HTTP response headers

---

## Phase 3: Email Intelligence

> **Input needed**: Target email addresses or domain name

### Step 3.1 - Email Security Assessment (DNS-based)

Check SPF, DKIM, and DMARC configuration via DNS TXT records.

```bash
# SPF record
dig +short TXT example.com | grep spf

# DMARC record
dig +short TXT _dmarc.example.com

# DKIM (try common selectors)
for selector in default google selector1 selector2 k1 mail s1 s2 dkim; do
    result=$(dig +short TXT ${selector}._domainkey.example.com 2>/dev/null)
    if [ -n "$result" ]; then
        echo "DKIM selector '${selector}': $result"
    fi
done

# MX records
dig +short MX example.com
```

**What to record**:
- Is SPF configured? Is it `~all` (softfail) or `-all` (hardfail)?
- Is DMARC configured? What's the policy (`none`/`quarantine`/`reject`)?
- Are DKIM records present for common selectors?
- Mail servers (MX records) — reveals email provider (Google Workspace, O365, self-hosted)

**Findings to flag**:
- Missing SPF/DMARC = email spoofing risk
- `p=none` DMARC policy = monitoring only, spoofing still possible
- Missing DKIM = email integrity not verified

---

### Step 3.2 - Breach Data Lookup (Have I Been Pwned)

> **Requires**: `HIBP_API_KEY` environment variable

Check if email addresses or the domain appear in known data breaches.

**For a specific email:**
```bash
curl -s -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/admin@example.com" | jq
```

**For a domain (all breaches involving that domain):**
```bash
curl -s -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breaches?domain=example.com" | jq
```

**What to record**:
- Which breaches include company emails
- Breach dates and types of data exposed (passwords, hashes, personal info)
- Number of affected accounts
- Whether password hashes were leaked (credential stuffing risk)

---

## Phase 4: Code & Repository Intelligence

> **Input needed**: GitHub organization name or repository URLs
>
> **To perform this step, you need**: The target's GitHub organization name (e.g., `example-corp`). This is often found on the company website, LinkedIn, or by searching GitHub for the company name.

### Step 4.1 - GitHub Organization Recon

> **Optional**: `GITHUB_API_TOKEN` for higher rate limits

```bash
# List public repos
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.github.com/orgs/example-corp/repos?per_page=100" | \
  jq -r '.[] | "\(.name) - \(.description) [\(.language)]"'

# List public members
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.github.com/orgs/example-corp/members?per_page=100" | \
  jq -r '.[].login'

# Search for secrets in code (limited to public repos)
curl -s "https://api.github.com/search/code?q=org:example-corp+password+extension:env" | \
  jq -r '.items[] | "\(.repository.full_name): \(.path)"'
```

**Interesting search queries:**
```
org:example-corp password extension:env
org:example-corp api_key extension:json
org:example-corp secret extension:yml
org:example-corp jdbc extension:properties
org:example-corp connectionstring extension:config
```

**What to record**:
- Repository names and descriptions (reveals technology stack)
- Programming languages used
- Public member usernames (useful for further OSINT)
- Any leaked credentials or API keys in code

---

### Step 4.2 - Secret Scanning in Repositories

Scan git history for accidentally committed secrets, API keys, passwords.

```bash
# TruffleHog — scans full git history
trufflehog git https://github.com/example-corp/app --json --only-verified

# Gitleaks — static analysis for secrets
gitleaks detect --source https://github.com/example-corp/app \
  --report-format json --report-path /dev/stdout
```

**What to record**:
- Any verified secrets (API keys, passwords, tokens)
- The commit hash and author (to understand timeline)
- Whether the secret has been rotated (check if still valid)

---

## Phase 5: Compile & Correlate Results

### Create a Master Asset Inventory

Combine all findings into a structured inventory:

```
SUBDOMAINS DISCOVERED:
  [source: crt.sh]       → staging.example.com, dev.example.com, ...
  [source: amass]         → api.example.com, mail.example.com, ...
  [source: theHarvester]  → vpn.example.com, ...
  Total unique:           → XX subdomains

IP ADDRESSES:
  [source: DNS/WHOIS]     → 198.51.100.42, 203.0.113.10, ...
  [source: Shodan]        → ports/services per IP
  Total unique:           → XX IPs

EMAIL ADDRESSES:
  [source: theHarvester]  → admin@example.com, dev@example.com, ...
  [source: HIBP]          → X emails in Y breaches
  Total unique:           → XX emails

TECHNOLOGIES:
  [source: Shodan]        → nginx 1.24, OpenSSH 8.9, ...
  [source: Wayback/GAU]   → PHP (.php URLs), Java (.jsp URLs), ...

SECURITY ISSUES (PASSIVE):
  - Email spoofing risk: Missing DMARC / SPF softfail
  - Credential exposure: X emails in data breaches
  - Secret leaks: API key found in repo commit abc123
  - Typosquat domains: X lookalike domains registered
```

### Prioritize for Active Phase

Based on passive findings, identify high-value targets for the active phase:
1. Subdomains with interesting names (staging, dev, admin, api, vpn)
2. IPs with many open ports (per Shodan)
3. Old/forgotten assets found via Wayback
4. Services running outdated software versions

---

## Quick Reference: All Passive Commands

```bash
# Domain intelligence
whois example.com
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u
amass enum -passive -d example.com
echo "example.com" | waybackurls | sort -u
gau example.com | sort -u
dnstwist --format json example.com
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,otx,rapiddns,urlscan

# IP intelligence
shodan host <IP>
shodan search hostname:example.com

# Email intelligence
dig +short TXT example.com | grep spf
dig +short TXT _dmarc.example.com
dig +short MX example.com
curl -s -H "hibp-api-key: KEY" "https://haveibeenpwned.com/api/v3/breachedaccount/user@example.com"

# Repository intelligence
trufflehog git https://github.com/org/repo --json --only-verified
gitleaks detect --source https://github.com/org/repo --report-format json --report-path /dev/stdout
```
