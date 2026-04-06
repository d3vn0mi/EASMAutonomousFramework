"""Seed AssessmentStep records for the Passive Recon guide v2."""
from django.db import migrations


PASSIVE_STEPS = [
    # Phase 1: Domain Intelligence
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.1",
        "title": "WHOIS Lookup",
        "description": (
            "Retrieve domain registration data: registrar, creation/expiry dates, nameservers, registrant info.\n\n"
            "What to record:\n"
            "- Registrar name and registration/expiry dates\n"
            "- Nameservers (reveal hosting provider)\n"
            "- Registrant organization and email (if not redacted)\n"
            "- Related domains under the same registrant\n\n"
            "Tip: If WHOIS privacy is enabled, the registrant org sometimes leaks in other fields. "
            "Cross-reference email addresses found here against HIBP."
        ),
        "commands": "whois example.com",
        "expected_input": "One or more target domain names",
        "expected_output": "Registrar, nameservers, registrant details, registration dates",
        "order": 10,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.2",
        "title": "ASN & IP Range Enumeration",
        "description": (
            "Discover all IP ranges owned by the target organization -- not just individual IPs.\n\n"
            "What to record:\n"
            "- ASN numbers owned by the org\n"
            "- All CIDR ranges associated (feeds Phase 2 -- scan these in Shodan)\n"
            "- Related ASNs for subsidiaries"
        ),
        "commands": (
            "# Find ASN by org name\n"
            "asnmap -org \"Example Corp\" -json\n\n"
            "# List all IPs in an ASN\n"
            "asnmap -a AS12345\n\n"
            "# Alternative via BGP data\n"
            "curl -s \"https://bgp.he.net/search?search[search]=example+corp&commit=Search\""
        ),
        "expected_input": "Target organization name",
        "expected_output": "ASN numbers, CIDR ranges owned by the organization",
        "order": 20,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.3",
        "title": "Certificate Transparency (crt.sh)",
        "description": (
            "Query public certificate transparency logs to discover subdomains that have had SSL certificates issued.\n\n"
            "What to record:\n"
            "- All discovered subdomains\n"
            "- Wildcard patterns (*.example.com)\n"
            "- Internal-looking names (staging, vpn, dev-api, jenkins, jira)"
        ),
        "commands": "curl -s \"https://crt.sh/?q=%.example.com&output=json\" | jq -r '.[].name_value' | sort -u",
        "expected_input": "Target domain name",
        "expected_output": "List of subdomains from certificate transparency logs",
        "order": 30,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.4",
        "title": "Passive Subdomain Enumeration",
        "description": (
            "Use multiple passive sources (DNS datasets, certificate logs, web archives) to find subdomains.\n\n"
            "Use -passive flag with Amass only. Without it, active DNS brute-forcing occurs.\n\n"
            "Resolve discovered subdomains to IPs -- this output feeds directly into Phase 2."
        ),
        "commands": (
            "# Amass (comprehensive, slower)\n"
            "amass enum -passive -d example.com\n\n"
            "# Subfinder (faster fallback)\n"
            "subfinder -d example.com -silent\n\n"
            "# Resolve subdomains to IPs\n"
            "cat subdomains.txt | dnsx -silent -a -resp"
        ),
        "expected_input": "Target domain name",
        "expected_output": "Subdomains list with resolved IP addresses",
        "order": 40,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.5",
        "title": "Historical URL Discovery (Wayback Machine)",
        "description": (
            "Retrieve URLs archived by the Wayback Machine and other web crawlers.\n\n"
            "What to record:\n"
            "- Old endpoints that may still be live (/admin, /api/v1, /backup)\n"
            "- File paths revealing technology stack (.php, .aspx, .jsp)\n"
            "- API endpoints and parameters\n"
            "- Config files (.env, .git/config, web.config)\n\n"
            "Probe which old URLs are still live using httpx."
        ),
        "commands": (
            "echo \"example.com\" | waybackurls | sort -u > wayback_urls.txt\n"
            "gau example.com | sort -u > gau_urls.txt\n\n"
            "# Filter for sensitive file extensions\n"
            "cat wayback_urls.txt gau_urls.txt | sort -u | \\\n"
            "  grep -iE '\\.(env|config|xml|json|sql|bak|old|zip|tar|gz|pem|key)$'\n\n"
            "# Filter for interesting paths\n"
            "cat wayback_urls.txt gau_urls.txt | sort -u | \\\n"
            "  grep -iE '(admin|login|dashboard|api|internal|staging|dev|backup|console)'\n\n"
            "# Probe which URLs are still live\n"
            "cat wayback_urls.txt gau_urls.txt | sort -u | httpx -silent -status-code -title"
        ),
        "expected_input": "Target domain name",
        "expected_output": "Historical URLs, sensitive file paths, live endpoints",
        "order": 50,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.6",
        "title": "Google Dorks",
        "description": (
            "Manual queries in Google -- no tools required, no packets sent to target.\n\n"
            "What to record:\n"
            "- Exposed documents revealing internal info\n"
            "- Admin panels indexed by Google\n"
            "- Pastebin entries referencing the domain\n"
            "- GitHub code referencing the domain (supplements Phase 4)"
        ),
        "commands": (
            "site:example.com filetype:pdf\n"
            "site:example.com filetype:xlsx OR filetype:csv\n"
            "site:example.com inurl:admin OR inurl:login OR inurl:dashboard\n"
            "site:example.com ext:sql OR ext:env OR ext:bak\n"
            "\"example.com\" ext:log\n"
            "\"@example.com\" filetype:pdf\n"
            "site:pastebin.com \"example.com\"\n"
            "site:github.com \"example.com\" password"
        ),
        "expected_input": "Target domain name",
        "expected_output": "Indexed documents, admin panels, pastebin entries, GitHub references",
        "order": 60,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.7",
        "title": "Typosquatting Detection (dnstwist)",
        "description": (
            "Identify domains that are visually similar to the target (phishing risk).\n\n"
            "What to record:\n"
            "- Registered lookalike domains resolving to IPs (actively used)\n"
            "- Domains with MX records (receiving email -- phishing risk)\n"
            "- Domains on known bulletproof hosting providers"
        ),
        "commands": "dnstwist --format json example.com | jq '.[] | select(.dns_a != null)'",
        "expected_input": "Target domain name",
        "expected_output": "Lookalike domains with DNS resolution and MX records",
        "order": 70,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.8",
        "title": "OSINT Harvesting (theHarvester)",
        "description": (
            "Gather emails, names, subdomains, and IPs from multiple public search engines and databases.\n\n"
            "hunter and intelx are among the best sources for email harvesting -- don't omit them.\n\n"
            "What to record:\n"
            "- Email addresses (feeds Phase 3)\n"
            "- Employee names (cross-reference with LinkedIn, feeds Phase 3)\n"
            "- Additional subdomains\n"
            "- IP addresses associated with the domain"
        ),
        "commands": "theHarvester -d example.com -b baidu,bing,crtsh,dnsdumpster,hackertarget,hunter,intelx,otx,rapiddns,urlscan",
        "expected_input": "Target domain name",
        "expected_output": "Email addresses, employee names, subdomains, IPs",
        "order": 80,
    },
    {
        "assessment_type": "passive",
        "phase_number": 1,
        "phase_name": "Domain Intelligence",
        "step_number": "1.9",
        "title": "LinkedIn OSINT",
        "description": (
            "Manual OSINT -- no tools required.\n\n"
            "1. Search site:linkedin.com/in \"example corp\" in Google\n"
            "2. Search the company page on LinkedIn for employees\n"
            "3. Note job postings -- technology mentions reveal stack\n\n"
            "What to record:\n"
            "- Employee names and roles (cross-reference with emails for phishing scope)\n"
            "- Technologies mentioned in job postings (We use Kubernetes, Terraform, AWS)\n"
            "- Recently departed employees (may retain access or have insider knowledge)"
        ),
        "commands": "# Manual: Search LinkedIn and Google\nsite:linkedin.com/in \"example corp\"",
        "expected_input": "Target organization name",
        "expected_output": "Employee names/roles, technology stack from job postings",
        "order": 90,
    },
    # Phase 2: IP & Infrastructure Intelligence
    {
        "assessment_type": "passive",
        "phase_number": 2,
        "phase_name": "IP & Infrastructure Intelligence",
        "step_number": "2.1",
        "title": "Shodan Lookup",
        "description": (
            "Query Shodan for banners, open ports, services, and technologies -- all collected passively by Shodan's crawlers.\n\n"
            "Use favicon hash to find related infrastructure across the internet.\n\n"
            "Fallback: Use Censys for complementary data -- different crawl schedule and additional TLS details.\n\n"
            "What to record:\n"
            "- Open ports and services\n"
            "- Software versions and banners\n"
            "- SSL/TLS certificate details\n"
            "- Known CVEs associated with detected versions\n"
            "- Cloud provider / hosting information\n"
            "- HTTP response headers (reveal frameworks, server versions)\n"
            "- Favicon hash matches (find related infrastructure)"
        ),
        "commands": (
            "# Single IP\n"
            "shodan host 198.51.100.42\n\n"
            "# Domain search\n"
            "shodan search hostname:example.com\n\n"
            "# ASN-wide search\n"
            "shodan search \"asn:AS12345\"\n\n"
            "# Favicon hash (finds related infrastructure)\n"
            "python3 -c \"\n"
            "import mmh3, requests\n"
            "r = requests.get('https://example.com/favicon.ico', timeout=5)\n"
            "print('Favicon hash:', mmh3.hash(r.content))\n"
            "\"\n"
            "# Then: shodan search http.favicon.hash:<HASH>"
        ),
        "expected_input": "IP addresses, CIDRs, or domain names from Phase 1",
        "expected_output": "Open ports, services, software versions, CVEs, hosting info",
        "order": 100,
    },
    # Phase 3: Email Intelligence
    {
        "assessment_type": "passive",
        "phase_number": 3,
        "phase_name": "Email Intelligence",
        "step_number": "3.1",
        "title": "Email Security Assessment",
        "description": (
            "Check SPF, DKIM, and DMARC configuration via DNS TXT records.\n\n"
            "Risk matrix:\n"
            "- No SPF record = High (anyone can spoof)\n"
            "- SPF ~all (softfail) = Medium (spoofed mail may be delivered)\n"
            "- SPF -all (hardfail) = Low (correct)\n"
            "- No DMARC = High (no enforcement)\n"
            "- DMARC p=none = Medium (monitoring only)\n"
            "- DMARC p=reject = Low (correct)\n"
            "- No DKIM = Medium (integrity not verified)"
        ),
        "commands": (
            "# SPF record\n"
            "dig +short TXT example.com | grep spf\n\n"
            "# DMARC record\n"
            "dig +short TXT _dmarc.example.com\n\n"
            "# DKIM (try common selectors)\n"
            "for selector in default google selector1 selector2 k1 mail s1 s2 dkim; do\n"
            "    result=$(dig +short TXT ${selector}._domainkey.example.com 2>/dev/null)\n"
            "    if [ -n \"$result\" ]; then\n"
            "        echo \"DKIM selector '${selector}': $result\"\n"
            "    fi\n"
            "done\n\n"
            "# MX records\n"
            "dig +short MX example.com"
        ),
        "expected_input": "Target domain name",
        "expected_output": "SPF, DMARC, DKIM records and risk assessment",
        "order": 110,
    },
    {
        "assessment_type": "passive",
        "phase_number": 3,
        "phase_name": "Email Intelligence",
        "step_number": "3.2",
        "title": "Breach Data Lookup (HIBP)",
        "description": (
            "Check if email addresses or the domain appear in known data breaches.\n\n"
            "Additional sources: dehashed.com, psbdmp.ws, intelx.io\n\n"
            "What to record:\n"
            "- Which breaches include company emails\n"
            "- Breach dates and data types exposed (passwords, hashes, PII)\n"
            "- Whether plaintext passwords or hashes were leaked (credential stuffing risk)\n"
            "- Number of affected accounts"
        ),
        "commands": (
            "# Single email\n"
            "curl -s -H \"hibp-api-key: YOUR_KEY\" \\\n"
            "  \"https://haveibeenpwned.com/api/v3/breachedaccount/admin@example.com\" | jq\n\n"
            "# Domain-wide breach check\n"
            "curl -s -H \"hibp-api-key: YOUR_KEY\" \\\n"
            "  \"https://haveibeenpwned.com/api/v3/breaches?domain=example.com\" | jq"
        ),
        "expected_input": "Email addresses from Phase 1, target domain",
        "expected_output": "Breach names, dates, data types exposed, affected accounts",
        "order": 120,
    },
    # Phase 4: Code & Repository Intelligence
    {
        "assessment_type": "passive",
        "phase_number": 4,
        "phase_name": "Code & Repository Intelligence",
        "step_number": "4.1",
        "title": "GitHub Organization Recon",
        "description": (
            "Enumerate public repositories, members, and search for secrets in code.\n\n"
            "What to record:\n"
            "- Repository names and descriptions (reveals technology stack)\n"
            "- Programming languages used\n"
            "- Public member usernames (useful for further OSINT)\n"
            "- Any leaked credentials or API keys in code"
        ),
        "commands": (
            "# List all public repos\n"
            "curl -s -H \"Authorization: Bearer YOUR_TOKEN\" \\\n"
            "  \"https://api.github.com/orgs/example-corp/repos?per_page=100\" | \\\n"
            "  jq -r '.[] | \"\\(.name) - \\(.description) [\\(.language)]\"'\n\n"
            "# List public members\n"
            "curl -s -H \"Authorization: Bearer YOUR_TOKEN\" \\\n"
            "  \"https://api.github.com/orgs/example-corp/members?per_page=100\" | \\\n"
            "  jq -r '.[].login'\n\n"
            "# GitHub code search queries:\n"
            "# org:example-corp password extension:env\n"
            "# org:example-corp api_key extension:json\n"
            "# org:example-corp secret extension:yml\n"
            "# org:example-corp \"BEGIN RSA PRIVATE KEY\"\n"
            "# org:example-corp \"AWS_ACCESS_KEY_ID\""
        ),
        "expected_input": "GitHub organization name (from company website, LinkedIn, or Google)",
        "expected_output": "Repository list, member usernames, potential secret locations",
        "order": 130,
    },
    {
        "assessment_type": "passive",
        "phase_number": 4,
        "phase_name": "Code & Repository Intelligence",
        "step_number": "4.2",
        "title": "Secret Scanning (Run Both Tools)",
        "description": (
            "Scan git history for accidentally committed secrets, API keys, passwords.\n\n"
            "Run BOTH TruffleHog and Gitleaks -- they use different detection patterns and one often catches "
            "what the other misses.\n\n"
            "What to record:\n"
            "- Any verified secrets (API keys, passwords, tokens)\n"
            "- Commit hash and author (understand timeline and who had access)\n"
            "- Whether the secret has been rotated (check if still valid)\n"
            "- Repository name and age (old archived repos are often overlooked)"
        ),
        "commands": (
            "# TruffleHog -- scans entire org, verifies secrets are live\n"
            "trufflehog github --org=example-corp --json --only-verified\n\n"
            "# TruffleHog on a single repo\n"
            "trufflehog git https://github.com/example-corp/app --json --only-verified\n\n"
            "# Gitleaks -- static analysis, different detection patterns\n"
            "gitleaks detect --source https://github.com/example-corp/app \\\n"
            "  --report-format json --report-path gitleaks-report.json"
        ),
        "expected_input": "GitHub organization name or repository URLs",
        "expected_output": "Verified secrets, commit hashes, authors, secret types",
        "order": 140,
    },
    # Phase 5: Compile & Correlate
    {
        "assessment_type": "passive",
        "phase_number": 5,
        "phase_name": "Compile & Correlate Results",
        "step_number": "5.1",
        "title": "Compile Master Asset Inventory & Report",
        "description": (
            "Combine all findings into a structured inventory and produce the final report.\n\n"
            "Use the EASM Report Template to structure your findings.\n\n"
            "Compile:\n"
            "- All subdomains with sources and live status\n"
            "- IP addresses with ASN, ports, services, CVEs\n"
            "- Email addresses with breach status\n"
            "- Technologies identified from all sources\n"
            "- Cloud assets (S3, Azure, GCP)\n"
            "- All security findings categorized by severity (Critical/High/Medium/Low)\n\n"
            "Prioritize targets for the active phase:\n"
            "1. Subdomains with interesting names (staging, dev, admin, api, vpn)\n"
            "2. IPs with many open ports (per Shodan)\n"
            "3. Old/forgotten assets found via Wayback\n"
            "4. Services running outdated software with known CVEs\n"
            "5. Cloud storage (S3, Azure, GCP) -- often misconfigured"
        ),
        "commands": (
            "# Use the EASM Report Template available at:\n"
            "# /assessments/report-template/\n\n"
            "# Cloud asset discovery\n"
            "cloud_enum -k example-corp\n"
            "cloud_enum -k examplecorp\n"
            "cloud_enum -k example_corp"
        ),
        "expected_input": "All findings from Phases 1-4",
        "expected_output": "Complete EASM report with findings, risk scores, and recommendations",
        "order": 150,
    },
]


def seed_steps(apps, schema_editor):
    AssessmentStep = apps.get_model("assessments", "AssessmentStep")
    for step_data in PASSIVE_STEPS:
        AssessmentStep.objects.get_or_create(
            assessment_type=step_data["assessment_type"],
            step_number=step_data["step_number"],
            defaults=step_data,
        )


def unseed_steps(apps, schema_editor):
    AssessmentStep = apps.get_model("assessments", "AssessmentStep")
    AssessmentStep.objects.filter(assessment_type="passive").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_steps, unseed_steps),
    ]
