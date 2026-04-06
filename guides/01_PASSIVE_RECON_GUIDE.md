# RAVEN EASM - Passive Reconnaissance Guide v2.0

> **Legal Disclaimer**: This guide is intended for use **only on systems and domains you are explicitly authorized to test**. Unauthorized reconnaissance may violate computer crime laws in your jurisdiction. Always obtain written authorization before beginning any engagement.

---

## Overview

This guide covers **passive-only** information gathering techniques. Passive recon collects data from public sources, APIs, and databases **without directly touching** the target infrastructure. No packets are sent to target systems.

**Use this when**: You have authorization to research the target but NOT to actively scan their systems, or during the initial intelligence-gathering phase before active engagement.

---

## Quick Win Checklist

For time-constrained engagements, run these 5 commands first — they give the highest value in the shortest time:

```bash
# 1. Subdomain discovery via certificate transparency
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u

# 2. Email + subdomain harvesting
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,hunter,intelx,otx,rapiddns,urlscan

# 3. Email security posture
dig +short TXT example.com | grep spf && dig +short TXT _dmarc.example.com

# 4. Shodan infrastructure lookup
shodan search hostname:example.com

# 5. GitHub secret scanning
trufflehog github --org=example-corp --json --only-verified
```

---

## Phase Dependencies

```
Phase 1 (Domain Intel)
    |
    +-> Subdomains -----------------------------------------+
    +-> IPs (via DNS resolution) --> Phase 2 (IP Intel)     |
    +-> Email addresses ----------> Phase 3 (Email Intel)   |
    +-> Employee names -----------> Phase 3 (Email Intel)   |
                                                            |
Phase 2 (IP Intel)                                          |
    +-> Open ports/services --------------------------------+
                                                            |
Phase 3 (Email Intel)                                       |
    +-> Breach data ----------------------------------------+
                                                            |
Phase 4 (Code Intel)                                        |
    +-> Leaked credentials/keys ----------------------------+
                                                            v
                                            Phase 5 (Compile & Report)
```

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
| Hunter.io | [hunter.io/api](https://hunter.io/api) | Email harvesting |
| IntelX | [intelx.io](https://intelx.io) | Deep web/paste search |

### Tool Installation

All tools below are pre-installed in the RAVEN scanner container:

```bash
docker compose exec scanner bash
```

Or install individually on Kali/Debian:

```bash
# Go tools
go install github.com/tomnomnom/waybackurls@latest
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest

# Python tools
pip install shodan theHarvester dnstwist mmh3 requests

# System tools
apt install whois dnsutils amass trufflehog gitleaks cloud-enum
```

### Tool Fallbacks

| Primary | Fallback | Notes |
|---------|----------|-------|
| Amass | subfinder | Faster, fewer sources |
| theHarvester | recon-ng | More modular |
| trufflehog | gitleaks | Different detection patterns — run both |
| Shodan CLI | Censys | Different crawl data, complementary |

**Estimated time per phase**: Phase 1: 30-60 min | Phase 2: 15-30 min | Phase 3: 15 min | Phase 4: 30-60 min | Phase 5: 30 min

---

## Phase 1: Domain Intelligence

> **Input**: One or more target domain names
> **Output**: Subdomains, IPs, emails, employee names -> feeds Phases 2, 3, 4
> **Estimated time**: 30-60 minutes

### Step 1.1 - WHOIS Lookup

```bash
whois example.com
```

**What to record**:
- Registrar name and registration/expiry dates
- Nameservers (reveal hosting provider)
- Registrant organization and email (if not redacted)
- Related domains under the same registrant

**Tip**: If WHOIS privacy is enabled, the registrant org sometimes leaks in other fields. Cross-reference email addresses found here against HIBP.

---

### Step 1.2 - ASN & IP Range Enumeration

Discover all IP ranges owned by the target organization — not just individual IPs.

```bash
# Find ASN by org name
asnmap -org "Example Corp" -json

# List all IPs in an ASN
asnmap -a AS12345

# Alternative via BGP data
curl -s "https://bgp.he.net/search?search[search]=example+corp&commit=Search"
```

**What to record**:
- ASN numbers owned by the org
- All CIDR ranges associated (feeds Phase 2 — scan these in Shodan)
- Related ASNs for subsidiaries

---

### Step 1.3 - Certificate Transparency (crt.sh)

```bash
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u
```

**What to record**:
- All discovered subdomains
- Wildcard patterns (`*.example.com`)
- Internal-looking names (`staging`, `vpn`, `dev-api`, `jenkins`, `jira`)

---

### Step 1.4 - Passive Subdomain Enumeration

```bash
# Amass (comprehensive, slower)
amass enum -passive -d example.com

# Subfinder (faster fallback)
subfinder -d example.com -silent
```

> Use `-passive` flag with Amass only. Without it, active DNS brute-forcing occurs.

**Resolve discovered subdomains to IPs:**

```bash
# Pipe subdomain list through dnsx to get live IPs
cat subdomains.txt | dnsx -silent -a -resp
```

This output feeds directly into Phase 2.

---

### Step 1.5 - Historical URL Discovery (Wayback Machine)

```bash
echo "example.com" | waybackurls | sort -u > wayback_urls.txt
gau example.com | sort -u > gau_urls.txt
```

**Filter for high-value targets:**

```bash
# Sensitive file extensions
cat wayback_urls.txt gau_urls.txt | sort -u | \
  grep -iE '\.(env|config|xml|json|sql|bak|old|zip|tar|gz|pem|key)$'

# Interesting paths
cat wayback_urls.txt gau_urls.txt | sort -u | \
  grep -iE '(admin|login|dashboard|api|internal|staging|dev|backup|console)'
```

**Probe which old URLs are still live:**

```bash
cat wayback_urls.txt gau_urls.txt | sort -u | httpx -silent -status-code -title
```

---

### Step 1.6 - Google Dorks

Manual queries in Google — no tools required, no packets sent to target:

```
site:example.com filetype:pdf
site:example.com filetype:xlsx OR filetype:csv
site:example.com inurl:admin OR inurl:login OR inurl:dashboard
site:example.com ext:sql OR ext:env OR ext:bak
"example.com" ext:log
"@example.com" filetype:pdf
site:pastebin.com "example.com"
site:github.com "example.com" password
```

**What to record**:
- Exposed documents revealing internal info
- Admin panels indexed by Google
- Pastebin entries referencing the domain
- GitHub code referencing the domain (supplements Phase 4)

---

### Step 1.7 - Typosquatting Detection (dnstwist)

```bash
dnstwist --format json example.com | jq '.[] | select(.dns_a != null)'
```

**What to record**:
- Registered lookalike domains resolving to IPs (actively used)
- Domains with MX records (receiving email — phishing risk)
- Domains on known bulletproof hosting providers

---

### Step 1.8 - OSINT Harvesting (theHarvester)

```bash
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,hunter,intelx,otx,rapiddns,urlscan
```

> `hunter` and `intelx` are among the best sources for email harvesting — don't omit them.

**What to record**:
- Email addresses (feeds Phase 3)
- Employee names (cross-reference with LinkedIn, feeds Phase 3)
- Additional subdomains
- IP addresses associated with the domain

---

### Step 1.9 - LinkedIn OSINT

Manual, no tools required:

1. Search `site:linkedin.com/in "example corp"` in Google
2. Search the company page on LinkedIn for employees
3. Note job postings — technology mentions reveal stack

**What to record**:
- Employee names and roles (cross-reference with emails for phishing scope)
- Technologies mentioned in job postings (`We use Kubernetes, Terraform, AWS`)
- Recently departed employees (may retain access or have insider knowledge)

---

## Phase 2: IP & Infrastructure Intelligence

> **Input**: IPs/CIDRs from WHOIS, DNS resolution (Step 1.4), ASN enumeration (Step 1.2)
> **Output**: Open ports, services, banners, CVEs -> feeds Phase 5
> **Estimated time**: 15-30 minutes

### Step 2.1 - Shodan Lookup

```bash
# Single IP
shodan host 198.51.100.42

# Domain search
shodan search hostname:example.com

# ASN-wide search
shodan search "asn:AS12345"

# Search by favicon hash (finds related infrastructure)
python3 -c "
import mmh3, requests
r = requests.get('https://example.com/favicon.ico', timeout=5)
print('Favicon hash:', mmh3.hash(r.content))
"
# Then search: shodan search http.favicon.hash:<HASH>
```

**Python for bulk processing:**

```python
import shodan
api = shodan.Shodan("YOUR_API_KEY")

try:
    result = api.host("198.51.100.42")
    for item in result.get("data", []):
        print(f"Port {item['port']}: {item.get('product', 'unknown')} {item.get('version', '')}")
        print(f"  Banner: {item.get('data', '')[:200]}")
        if 'vulns' in item:
            for cve in item['vulns']:
                print(f"  CVE: {cve}")
except shodan.APIError as e:
    print(f"Shodan error: {e}")
```

> **Fallback**: Use [Censys](https://search.censys.io) for complementary data — different crawl schedule and additional TLS details.

**What to record**:
- Open ports and services
- Software versions and banners
- SSL/TLS certificate details
- Known CVEs associated with detected versions
- Cloud provider / hosting information
- HTTP response headers (reveal frameworks, server versions)
- Favicon hash matches (find related infrastructure across the internet)

---

## Phase 3: Email Intelligence

> **Input**: Email addresses and employee names from Phase 1
> **Output**: Breach data, email security posture -> feeds Phase 5
> **Estimated time**: 15 minutes

### Step 3.1 - Email Security Assessment

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

**Risk matrix**:

| Finding | Risk | Notes |
|---------|------|-------|
| No SPF record | High | Anyone can spoof the domain |
| SPF `~all` (softfail) | Medium | Spoofed mail may be delivered |
| SPF `-all` (hardfail) | Low | Correct configuration |
| No DMARC | High | No enforcement even with SPF/DKIM |
| DMARC `p=none` | Medium | Monitoring only, no enforcement |
| DMARC `p=reject` | Low | Correct configuration |
| No DKIM | Medium | Email integrity not verified |

---

### Step 3.2 - Breach Data Lookup (HIBP)

```bash
# Single email
curl -s -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/admin@example.com" | jq

# Domain-wide breach check
curl -s -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breaches?domain=example.com" | jq
```

**Additional sources:**
- [dehashed.com](https://dehashed.com) — leaked credential database
- [psbdmp.ws](https://psbdmp.ws) — Pastebin dumps search
- [intelx.io](https://intelx.io) — paste and dark web search

**What to record**:
- Which breaches include company emails
- Breach dates and data types exposed (passwords, hashes, PII)
- Whether plaintext passwords or hashes were leaked (credential stuffing risk)
- Number of affected accounts

---

## Phase 4: Code & Repository Intelligence

> **Input**: GitHub org name (from company website, LinkedIn, or Google: `site:github.com "example corp"`)
> **Output**: Leaked credentials, API keys, infrastructure details -> feeds Phase 5
> **Estimated time**: 30-60 minutes

### Step 4.1 - GitHub Organization Recon

```bash
# List all public repos
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.github.com/orgs/example-corp/repos?per_page=100" | \
  jq -r '.[] | "\(.name) - \(.description) [\(.language)]"'

# List public members (cross-reference with Phase 1 employee names)
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.github.com/orgs/example-corp/members?per_page=100" | \
  jq -r '.[].login'
```

**GitHub code search queries:**

```
org:example-corp password extension:env
org:example-corp api_key extension:json
org:example-corp secret extension:yml
org:example-corp jdbc extension:properties
org:example-corp connectionstring extension:config
org:example-corp "BEGIN RSA PRIVATE KEY"
org:example-corp "AWS_ACCESS_KEY_ID"
```

---

### Step 4.2 - Secret Scanning (Run Both Tools)

```bash
# TruffleHog — scans entire org at once, verifies secrets are live
trufflehog github --org=example-corp --json --only-verified

# TruffleHog on a single repo
trufflehog git https://github.com/example-corp/app --json --only-verified

# Gitleaks — static analysis, different detection patterns
gitleaks detect --source https://github.com/example-corp/app \
  --report-format json --report-path gitleaks-report.json
```

> Run **both** TruffleHog and Gitleaks — they use different detection patterns and one often catches what the other misses.

**What to record**:
- Any verified secrets (API keys, passwords, tokens)
- Commit hash and author (understand timeline and who had access)
- Whether the secret has been rotated (check if still valid against the service)
- Repository name and age (old archived repos are often overlooked)

---

## Phase 5: Compile & Correlate Results

> **Estimated time**: 30 minutes

### Master Asset Inventory Template

```
=====================================================
RAVEN EASM - Passive Recon Report
Target: example.com
Date: YYYY-MM-DD
Operator: [name]
=====================================================

SUBDOMAINS DISCOVERED:
  [crt.sh]        -> staging.example.com, dev.example.com, ...
  [amass]         -> api.example.com, mail.example.com, ...
  [theHarvester]  -> vpn.example.com, ...
  Total unique:   -> XX subdomains
  Live (httpx):   -> XX responding

IP ADDRESSES & ASNs:
  ASN:            -> AS12345 (Example Corp) - XX IPs
  [DNS/dnsx]      -> 198.51.100.42, 203.0.113.10, ...
  [Shodan]        -> ports/services/CVEs per IP
  Total unique:   -> XX IPs

EMAIL ADDRESSES:
  [theHarvester]  -> admin@example.com, dev@example.com, ...
  [HIBP]          -> X emails in Y breaches
  Total unique:   -> XX emails

TECHNOLOGIES IDENTIFIED:
  [Shodan]        -> nginx 1.24, OpenSSH 8.9, ...
  [Wayback/GAU]   -> PHP (.php URLs), Java (.jsp URLs), ...
  [LinkedIn/jobs] -> AWS, Kubernetes, Terraform, ...

CLOUD ASSETS:
  S3 buckets:     -> example-corp-assets.s3.amazonaws.com
  Azure blobs:    -> none found
  GCP buckets:    -> none found

SECURITY FINDINGS:
  CRITICAL:
    [ ] Leaked API key in GitHub commit abc123 (repo: example-corp/app)
    [ ] Plaintext passwords in breach: Collection #1 (2019)
  HIGH:
    [ ] No DMARC policy -- email spoofing risk
    [ ] SPF softfail (~all) -- spoofed mail may be delivered
  MEDIUM:
    [ ] X typosquat domains registered with MX records
    [ ] Outdated software: nginx 1.18 (EOL) on 198.51.100.42
  LOW:
    [ ] X subdomains exposing internal naming (staging, dev, vpn)
```

---

### Risk Scoring Matrix

| Severity | Examples | Action |
|----------|---------|--------|
| **Critical** | Live API keys, plaintext passwords, private keys in repos | Immediate escalation to client |
| **High** | Missing DMARC, passwords in breach data, exposed admin panels | Priority in active phase |
| **Medium** | SPF softfail, outdated software versions, typosquat domains | Include in report recommendations |
| **Low** | Internal subdomain naming, old archived URLs | Informational |

---

### Prioritize for Active Phase

Based on passive findings, rank targets for active scanning:

1. **Subdomains with interesting names** (`staging`, `dev`, `admin`, `api`, `vpn`, `jenkins`, `jira`)
2. **IPs with many open ports** (per Shodan) — larger attack surface
3. **Old/forgotten assets** found via Wayback Machine
4. **Services running outdated software** with known CVEs
5. **Cloud storage** (S3, Azure, GCP) — often misconfigured

---

## Quick Reference: All Passive Commands

```bash
# -- DOMAIN INTELLIGENCE -------------------------------------------------------
whois example.com
asnmap -org "Example Corp" -json
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u
amass enum -passive -d example.com
subfinder -d example.com -silent
cat subdomains.txt | dnsx -silent -a -resp
echo "example.com" | waybackurls | sort -u > wayback_urls.txt
gau example.com | sort -u > gau_urls.txt
cat wayback_urls.txt gau_urls.txt | sort -u | httpx -silent -status-code -title
dnstwist --format json example.com | jq '.[] | select(.dns_a != null)'
theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,hunter,intelx,otx,rapiddns,urlscan

# -- IP INTELLIGENCE ------------------------------------------------------------
shodan host <IP>
shodan search hostname:example.com
shodan search "asn:AS12345"
# Favicon hash -> shodan search http.favicon.hash:<HASH>

# -- EMAIL INTELLIGENCE ---------------------------------------------------------
dig +short TXT example.com | grep spf
dig +short TXT _dmarc.example.com
dig +short MX example.com
curl -s -H "hibp-api-key: KEY" "https://haveibeenpwned.com/api/v3/breachedaccount/user@example.com"
curl -s -H "hibp-api-key: KEY" "https://haveibeenpwned.com/api/v3/breaches?domain=example.com"

# -- CODE INTELLIGENCE ----------------------------------------------------------
trufflehog github --org=example-corp --json --only-verified
trufflehog git https://github.com/example-corp/repo --json --only-verified
gitleaks detect --source https://github.com/example-corp/repo --report-format json --report-path /dev/stdout

# -- CLOUD ASSET DISCOVERY ------------------------------------------------------
cloud_enum -k example-corp
cloud_enum -k examplecorp
cloud_enum -k example_corp
```
