# RAVEN EASM - Full Reconnaissance Guide (Passive + Active)

## Overview

This guide covers the **complete** EASM reconnaissance methodology: passive intelligence gathering followed by active scanning and vulnerability assessment. Active techniques send packets directly to target systems.

**Use this when**: You have **written authorization** (Statement of Work / Rules of Engagement) to actively scan the target's infrastructure.

> **WARNING**: Active scanning without authorization is illegal in most jurisdictions. Ensure you have explicit written permission before proceeding with any active steps (marked with [ACTIVE]).

---

## Prerequisites

### Required Inputs

| Input | Example | Required? |
|-------|---------|-----------|
| Target domains | `example.com`, `corp.example.com` | At least one |
| Target IPs/CIDRs | `203.0.113.0/24`, `198.51.100.42` | Optional |
| Email addresses | `admin@example.com` | Optional |
| URLs | `https://app.example.com` | Optional |
| GitHub org name | `example-corp` | Optional |
| Git repository URLs | `https://github.com/example-corp/app` | Optional |

### API Keys

| Service | How to Get | What It Unlocks |
|---------|-----------|-----------------|
| Shodan | [account.shodan.io](https://account.shodan.io) | Passive port/service/banner data |
| HIBP | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) | Breach data for emails/domains |
| GitHub | GitHub > Settings > Developer Settings > PAT | Higher API rate limits |

### Tool Access

All tools are pre-installed in the RAVEN scanner container:

```bash
docker compose exec scanner bash
```

> **Note**: The scanner container has `NET_ADMIN` and `NET_RAW` capabilities for nmap/masscan.

### Wordlists

Pre-installed at `/opt/seclists/`:
```
/opt/seclists/Discovery/Web-Content/common.txt          # 4,700 entries
/opt/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt  # 220,000 entries
/opt/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

---

## Phase 1: Passive Intelligence [NO TARGET INTERACTION]

> All steps in this phase use public data sources. No packets are sent to target systems.

### Step 1.1 - WHOIS [PASSIVE]

```bash
whois example.com
```

**Record**: Registrar, dates, nameservers, registrant info, related domains.

---

### Step 1.2 - Certificate Transparency [PASSIVE]

```bash
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u > subdomains_crtsh.txt
```

**Record**: All subdomains from SSL certificate issuance logs.

---

### Step 1.3 - Passive Subdomain Enumeration [PASSIVE]

```bash
# Amass — multiple passive data sources
amass enum -passive -d example.com | tee subdomains_amass.txt

# theHarvester — search engines, DNS dumps, certificate logs
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,otx,rapiddns,urlscan
```

**Record**: Subdomains, email addresses, IP addresses from search engine results.

---

### Step 1.4 - Historical URL Discovery [PASSIVE]

```bash
echo "example.com" | waybackurls | sort -u > wayback_urls.txt
gau example.com | sort -u > gau_urls.txt

# Combine and find interesting files
cat wayback_urls.txt gau_urls.txt | sort -u > all_historical_urls.txt
grep -iE '\.(env|config|xml|json|sql|bak|old|zip|tar|gz|log|swp)$' all_historical_urls.txt > interesting_files.txt
grep -iE '(admin|login|dashboard|api|internal|staging|dev|debug|phpinfo|test)' all_historical_urls.txt > interesting_paths.txt
```

---

### Step 1.5 - Typosquatting Detection [PASSIVE]

```bash
dnstwist --format json example.com | jq '.[] | select(.dns_a != null)'
```

**Record**: Registered lookalike domains with active DNS records.

---

### Step 1.6 - Shodan Intelligence [PASSIVE]

> **Requires**: `SHODAN_API_KEY`

```bash
# Per IP
shodan host 198.51.100.42

# Per domain
shodan search hostname:example.com --fields ip_str,port,product,version
```

**Record**: Open ports, services, versions, banners — all without touching the target.

---

### Step 1.7 - Email Security (DNS) [PASSIVE]

```bash
# SPF
dig +short TXT example.com | grep spf

# DMARC
dig +short TXT _dmarc.example.com

# DKIM (common selectors)
for sel in default google selector1 selector2 k1 mail s1 s2 dkim; do
    r=$(dig +short TXT ${sel}._domainkey.example.com 2>/dev/null)
    [ -n "$r" ] && echo "DKIM [$sel]: $r"
done

# MX
dig +short MX example.com
```

**Flag**: Missing SPF, missing DMARC, `p=none` policy, missing DKIM.

---

### Step 1.8 - Breach Data [PASSIVE]

> **Requires**: `HIBP_API_KEY`

```bash
# Per email
curl -s -H "hibp-api-key: $HIBP_API_KEY" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/admin@example.com" | jq '.[].Name'

# Per domain
curl -s -H "hibp-api-key: $HIBP_API_KEY" \
  "https://haveibeenpwned.com/api/v3/breaches?domain=example.com" | jq '.[].Name'
```

---

### Step 1.9 - GitHub / Repository Recon [PASSIVE]

> **To perform this step, you need**: The target's GitHub organization name. Find it on the company website footer, LinkedIn, or search GitHub directly.

```bash
# List repos
curl -s -H "Authorization: Bearer $GITHUB_API_TOKEN" \
  "https://api.github.com/orgs/ORGNAME/repos?per_page=100" | \
  jq -r '.[] | "\(.full_name) [\(.language)] - \(.description)"'

# Search for secrets in code
curl -s "https://api.github.com/search/code?q=org:ORGNAME+password+extension:env" | \
  jq -r '.items[] | "\(.repository.full_name): \(.path)"'
```

**Secret scanning:**
```bash
trufflehog git https://github.com/ORGNAME/REPO --json --only-verified
gitleaks detect --source https://github.com/ORGNAME/REPO --report-format json --report-path /dev/stdout
```

---

### Passive Phase Checkpoint

Before proceeding to active scanning, compile your passive findings:

```
COMPILE: Master subdomain list
cat subdomains_crtsh.txt subdomains_amass.txt | sort -u > all_subdomains.txt
echo "Total unique subdomains: $(wc -l < all_subdomains.txt)"
```

**Review your scope**: Confirm all discovered subdomains/IPs fall within the authorized scope before active scanning.

---

## Phase 2: Active Discovery [TARGET INTERACTION]

> **From this point forward, all steps actively interact with target systems.**

### Step 2.1 - Active Subdomain Discovery [ACTIVE]

These tools make DNS queries and HTTP connections to verify subdomain existence.

```bash
# Subfinder — queries multiple sources, some involve DNS resolution
subfinder -d example.com -silent | tee subdomains_subfinder.txt

# Assetfinder — finds related domains/subdomains
assetfinder --subs-only example.com | tee subdomains_assetfinder.txt

# Merge all subdomain lists
cat all_subdomains.txt subdomains_subfinder.txt subdomains_assetfinder.txt | sort -u > all_subdomains_final.txt
echo "Total subdomains after active discovery: $(wc -l < all_subdomains_final.txt)"
```

---

### Step 2.2 - HTTP Probing [ACTIVE]

Determine which subdomains have live web servers, their status codes, titles, and technologies.

```bash
httpx -l all_subdomains_final.txt -silent -status-code -title -tech-detect -json -o httpx_results.json
```

Or for a single target:
```bash
httpx -u example.com -silent -status-code -title -tech-detect -json
```

**What to record**:
- Live hosts (HTTP 200, 301, 302, 403)
- Page titles (reveal application purpose)
- Detected technologies (frameworks, CMS, server software)
- Redirect chains

**Filter live hosts:**
```bash
cat httpx_results.json | jq -r 'select(.status_code == 200) | .url' > live_urls.txt
```

---

### Step 2.3 - Web Technology Fingerprinting [ACTIVE]

```bash
# For each live URL
while read url; do
    echo "=== $url ==="
    whatweb --log-json=- --color=never "$url"
done < live_urls.txt
```

Or for a single target:
```bash
whatweb --log-json=- --color=never https://example.com
```

**What to record**: CMS versions, programming languages, frameworks, server headers, JavaScript libraries.

---

### Step 2.4 - WAF Detection [ACTIVE]

```bash
while read url; do
    echo "=== $url ==="
    wafw00f "$url"
done < live_urls.txt
```

**What to record**: WAF product and version (Cloudflare, AWS WAF, Akamai, ModSecurity, etc.). This informs how aggressive your scanning can be.

---

### Step 2.5 - Screenshots [ACTIVE]

Capture visual screenshots of all live web endpoints for quick review.

```bash
while read url; do
    gowitness single "$url" --screenshot-path ./screenshots --chrome-path /usr/bin/chromium
done < live_urls.txt
```

**What to record**: Visual state of each application — login pages, dashboards, error pages, default installs, admin panels.

---

## Phase 3: Active Port Scanning [TARGET INTERACTION]

### Step 3.1 - Fast Port Discovery (IPs/CIDRs) [ACTIVE]

> **For CIDR ranges**: Use masscan first for speed, then nmap for service detection on discovered ports.

```bash
# Fast SYN scan of all 65535 ports (for CIDR ranges)
masscan 203.0.113.0/24 -p 1-65535 --rate 1000 -oJ masscan_results.json

# Extract open ports
cat masscan_results.json | jq -r '.[] | "\(.ip):\(.ports[0].port)"' | sort -u
```

> **Note**: masscan requires root/NET_ADMIN capability. Adjust `--rate` based on network conditions. Start with `--rate 500` if unsure.

---

### Step 3.2 - Service Detection (nmap) [ACTIVE]

**For individual IPs or domains (Bronze — top 1000 ports):**
```bash
nmap -T4 --top-ports 1000 -sV --open example.com
```

**For thorough scanning (Silver/Gold — all ports):**
```bash
nmap -T4 -p 1-65535 -sV --open example.com
```

**For IPs discovered by masscan (targeted scan):**
```bash
# Scan only the ports masscan found open
nmap -T4 -p 22,80,443,8080,8443 -sV --open 198.51.100.42
```

**What to record**:
- Open ports and services
- Software names and version numbers
- Operating system hints
- Unusual ports (development servers, databases exposed)

---

### Step 3.3 - SSL/TLS Assessment [ACTIVE]

> **Input needed**: Hostnames or IPs with HTTPS services (from httpx or nmap results)

```bash
testssl --jsonfile=- --warnings off example.com:443
```

**What to record and flag**:
- SSL/TLS protocol versions (flag SSLv3, TLS 1.0, TLS 1.1 as deprecated)
- Weak cipher suites (RC4, DES, NULL, export-grade)
- Certificate validity, expiry, chain issues
- Known vulnerabilities: Heartbleed, POODLE, ROBOT, CRIME, BREACH
- Missing HSTS header
- Certificate mismatch (CN/SAN vs hostname)

---

## Phase 4: Vulnerability Assessment [TARGET INTERACTION]

### Step 4.1 - Automated Vulnerability Scanning (Nuclei) [ACTIVE]

**Standard scan (Bronze/Silver — critical/high/medium):**
```bash
nuclei -u https://example.com -severity critical,high,medium -jsonl -silent
```

**Thorough scan (Gold — includes low severity):**
```bash
nuclei -u https://example.com -severity critical,high,medium,low -jsonl -silent
```

**Batch scan all live URLs:**
```bash
nuclei -l live_urls.txt -severity critical,high,medium -jsonl -silent -o nuclei_results.jsonl
```

> **Tip**: Update templates before scanning:
> ```bash
> nuclei -update-templates
> ```

**What to record**:
- Vulnerability template ID and name
- Severity (critical/high/medium/low)
- Matched URL and evidence
- CVE references if available
- Remediation guidance (included in template metadata)

---

### Step 4.2 - Directory & File Discovery (Feroxbuster) [ACTIVE]

> **This is an aggressive scan** — it makes thousands of HTTP requests. Only use on authorized targets.

```bash
# Standard wordlist
feroxbuster -u https://example.com --json --silent \
  -w /opt/seclists/Discovery/Web-Content/common.txt

# Larger wordlist (more thorough, much slower)
feroxbuster -u https://example.com --json --silent \
  -w /opt/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  -d 2    # recursion depth
```

**What to record**:
- Discovered directories and files (200, 301, 302, 403 responses)
- Admin panels, backup files, config files
- API endpoints
- Any 403 Forbidden responses (potential access control bypass targets)

---

## Phase 5: Scope-Specific Workflows

### For Domain Scope

Run these steps in order:

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | subfinder | ACTIVE | `subfinder -d DOMAIN -silent` |
| 2 | amass | PASSIVE | `amass enum -passive -d DOMAIN` |
| 3 | assetfinder | ACTIVE | `assetfinder --subs-only DOMAIN` |
| 4 | crt.sh | PASSIVE | `curl -s "https://crt.sh/?q=%.DOMAIN&output=json"` |
| 5 | whois | PASSIVE | `whois DOMAIN` |
| 6 | theHarvester | PASSIVE | `theHarvester -d DOMAIN -b baidu,bing,crtsh,...` |
| 7 | httpx | ACTIVE | `httpx -u DOMAIN -silent -status-code -title -tech-detect -json` |
| 8 | nmap | ACTIVE | `nmap -T4 -p 1-65535 -sV --open DOMAIN` |
| 9 | nuclei | ACTIVE | `nuclei -u https://DOMAIN -severity critical,high,medium -jsonl -silent` |
| 10 | whatweb | ACTIVE | `whatweb --log-json=- --color=never https://DOMAIN` |
| 11 | gowitness | ACTIVE | `gowitness single https://DOMAIN --screenshot-path ./screenshots` |
| 12 | testssl | ACTIVE | `testssl --jsonfile=- --warnings off DOMAIN:443` |
| 13 | wafw00f | ACTIVE | `wafw00f https://DOMAIN` |
| 14 | waybackurls | PASSIVE | `echo DOMAIN \| waybackurls` |
| 15 | gau | PASSIVE | `gau DOMAIN` |
| 16 | dnstwist | PASSIVE | `dnstwist --format json DOMAIN` |
| 17 | shodan | PASSIVE | `shodan host IP` or `shodan search hostname:DOMAIN` |
| 18 | feroxbuster | ACTIVE | `feroxbuster -u https://DOMAIN --json --silent -w /opt/seclists/...` |

---

### For IP Scope

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | nmap | ACTIVE | `nmap -T4 -p 1-65535 -sV --open IP` |
| 2 | nuclei | ACTIVE | `nuclei -u https://IP -severity critical,high,medium -jsonl -silent` |
| 3 | shodan | PASSIVE | `shodan host IP` |

---

### For CIDR Scope

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | masscan | ACTIVE | `masscan CIDR -p 1-65535 --rate 1000 -oJ -` |
| 2 | nmap | ACTIVE | `nmap -T4 -p PORTS -sV --open IP` (per discovered host) |
| 3 | shodan | PASSIVE | `shodan host IP` (per host) |
| 4 | httpx | ACTIVE | `httpx -u IP -silent -status-code -title -tech-detect -json` |
| 5 | nuclei | ACTIVE | `nuclei -u https://IP -severity critical,high,medium -jsonl -silent` |
| 6 | gowitness | ACTIVE | `gowitness single https://IP --screenshot-path ./screenshots` |
| 7 | whatweb | ACTIVE | `whatweb --log-json=- --color=never https://IP` |

---

### For Email Scope

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | theHarvester | PASSIVE | `theHarvester -d DOMAIN -b ...` |
| 2 | Email security | PASSIVE | `dig TXT _dmarc.DOMAIN`, `dig TXT DOMAIN` (SPF) |
| 3 | HIBP | PASSIVE | `curl -H "hibp-api-key: KEY" haveibeenpwned.com/api/v3/...` |

---

### For URL Scope

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | httpx | ACTIVE | `httpx -u URL -silent -status-code -title -tech-detect -json` |
| 2 | whatweb | ACTIVE | `whatweb --log-json=- --color=never URL` |
| 3 | nuclei | ACTIVE | `nuclei -u URL -severity critical,high,medium -jsonl -silent` |
| 4 | feroxbuster | ACTIVE | `feroxbuster -u URL --json --silent -w ...` |
| 5 | gowitness | ACTIVE | `gowitness single URL --screenshot-path ./screenshots` |
| 6 | testssl | ACTIVE | `testssl --jsonfile=- --warnings off URL` |
| 7 | wafw00f | ACTIVE | `wafw00f URL` |

---

### For Repository Scope

> **To perform this step, you need**: Git repository URL (HTTPS or SSH format)

| # | Tool | Type | Command |
|---|------|------|---------|
| 1 | trufflehog | PASSIVE* | `trufflehog git REPO_URL --json --only-verified` |
| 2 | gitleaks | PASSIVE* | `gitleaks detect --source REPO_URL --report-format json --report-path /dev/stdout` |

*These tools clone the repo and scan git history — they don't interact with the target infrastructure itself.

---

## Phase 6: Findings Classification

### Severity Matrix

| Severity | Examples |
|----------|---------|
| **Critical** | RCE, SQL injection, exposed admin panel with default creds, leaked production secrets |
| **High** | SSRF, authentication bypass, exposed sensitive data, unpatched CVEs with public exploits |
| **Medium** | XSS, CSRF, information disclosure, weak SSL/TLS, missing security headers |
| **Low** | Version disclosure, directory listing, verbose errors, deprecated TLS versions |
| **Info** | Technology fingerprints, open ports (expected), DNS records |

### Common Finding Categories

**From Nuclei**: CVEs, misconfigurations, default credentials, exposed panels, information disclosure

**From Testssl**: Weak protocols (TLS 1.0/1.1), weak ciphers, certificate issues, missing HSTS

**From Email Security**: Missing SPF/DMARC/DKIM, email spoofing risk

**From Secret Scanning**: Leaked API keys, passwords, tokens in git history

**From Feroxbuster**: Exposed admin panels, backup files, config files, debug endpoints

**From HIBP**: Credential exposure in data breaches

---

## Phase 7: Compile Report

### Structure your findings as:

```
1. EXECUTIVE SUMMARY
   - Scope overview
   - Key risk highlights
   - Top 5 critical findings

2. ATTACK SURFACE OVERVIEW
   - Total subdomains: XX
   - Total live hosts: XX
   - Total open ports: XX
   - Total unique services: XX

3. FINDINGS (by severity)
   For each finding:
   - Title
   - Severity + CVSS score
   - Affected asset(s)
   - Description
   - Evidence / proof
   - Recommendation
   - References

4. APPENDICES
   - Full subdomain list
   - Full port scan results
   - Tool output logs
```

---

## Quick Reference: Complete Command Cheat Sheet

```bash
# ═══ PASSIVE ═══════════════════════════════════════════════════════════
whois example.com
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u
amass enum -passive -d example.com
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,otx,rapiddns,urlscan
echo "example.com" | waybackurls | sort -u
gau example.com | sort -u
dnstwist --format json example.com
shodan host <IP>
dig +short TXT example.com | grep spf
dig +short TXT _dmarc.example.com
curl -s -H "hibp-api-key: KEY" "https://haveibeenpwned.com/api/v3/breachedaccount/EMAIL"
trufflehog git REPO_URL --json --only-verified
gitleaks detect --source REPO_URL --report-format json --report-path /dev/stdout

# ═══ ACTIVE ════════════════════════════════════════════════════════════
subfinder -d example.com -silent
assetfinder --subs-only example.com
httpx -u example.com -silent -status-code -title -tech-detect -json
nmap -T4 -p 1-65535 -sV --open example.com
masscan 203.0.113.0/24 -p 1-65535 --rate 1000 -oJ -
nuclei -u https://example.com -severity critical,high,medium -jsonl -silent
whatweb --log-json=- --color=never https://example.com
wafw00f https://example.com
gowitness single https://example.com --screenshot-path ./screenshots --chrome-path /usr/bin/chromium
testssl --jsonfile=- --warnings off example.com:443
feroxbuster -u https://example.com --json --silent -w /opt/seclists/Discovery/Web-Content/common.txt
```
