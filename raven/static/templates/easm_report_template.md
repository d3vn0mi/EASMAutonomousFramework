# EASM Passive Reconnaissance Report

---

## 1. Executive Summary

**Assessment Name**: [Assessment Name]
**Assessment Type**: Passive Reconnaissance
**Overall Risk Rating**: [Critical / High / Medium / Low]

Provide a brief (2-3 paragraph) executive summary describing:
- The purpose of the assessment
- High-level findings and risk posture
- Key recommendations

---

## 2. Engagement Details

| Field | Value |
|-------|-------|
| **Client** | [Client Name] |
| **Engagement ID** | [RAVEN-EASM-YYYY-NNN] |
| **Assessment Date** | [Start Date] - [End Date] |
| **Operator** | [Engineer Name] |
| **Scope** | See Section 2.1 |
| **Methodology** | RAVEN EASM Passive Reconnaissance Guide v2.0 |

### 2.1 Scope

List all in-scope targets:

| Type | Value | Notes |
|------|-------|-------|
| Domain | example.com | Primary domain |
| Domain | corp.example.com | Corporate subdomain |
| CIDR | 203.0.113.0/24 | Main IP range |
| Email | *@example.com | All company emails |
| GitHub Org | example-corp | Public repositories |

---

## 3. Methodology

This assessment followed the RAVEN EASM Passive Reconnaissance Guide v2.0, consisting of 5 phases:

1. **Domain Intelligence** - WHOIS, ASN enumeration, certificate transparency, subdomain discovery, historical URLs, Google dorking, typosquatting detection, OSINT harvesting, LinkedIn OSINT
2. **IP & Infrastructure Intelligence** - Shodan lookup, service/banner analysis, CVE identification
3. **Email Intelligence** - SPF/DKIM/DMARC assessment, breach data lookup
4. **Code & Repository Intelligence** - GitHub organization recon, secret scanning
5. **Compile & Correlate** - Asset inventory, risk scoring, prioritization

All techniques are passive only -- no packets were sent directly to target infrastructure.

---

## 4. Subdomains Discovered

**Total unique subdomains**: [XX]
**Live (responding to HTTP)**: [XX]

| Subdomain | Source | IP Address | Status | Notes |
|-----------|--------|------------|--------|-------|
| staging.example.com | crt.sh | 203.0.113.10 | 200 OK | Staging environment |
| dev.example.com | amass | 203.0.113.11 | 200 OK | Development |
| vpn.example.com | theHarvester | 203.0.113.12 | 403 | VPN gateway |
| api.example.com | subfinder | 203.0.113.13 | 200 OK | API endpoint |

### 4.1 Noteworthy Subdomains

List subdomains that warrant further investigation:
- `staging.example.com` - Staging environments often have weaker security controls
- `vpn.example.com` - VPN gateway, potential entry point
- `jenkins.example.com` - CI/CD system, may expose build artifacts

---

## 5. IP Addresses & ASN Information

### 5.1 ASN Summary

| ASN | Organization | CIDR Ranges | IP Count |
|-----|-------------|-------------|----------|
| AS12345 | Example Corp | 203.0.113.0/24 | 256 |

### 5.2 Host Details

| IP Address | Open Ports | Services | Software | CVEs |
|------------|-----------|----------|----------|------|
| 203.0.113.10 | 80, 443 | HTTP, HTTPS | nginx 1.24.0 | None |
| 203.0.113.11 | 22, 80, 443 | SSH, HTTP, HTTPS | OpenSSH 8.9, Apache 2.4.54 | CVE-2023-XXXXX |
| 203.0.113.12 | 443, 1194 | HTTPS, OpenVPN | OpenVPN 2.5.8 | None |

### 5.3 Cloud Infrastructure

| Provider | Asset Type | Identifier | Status |
|----------|-----------|------------|--------|
| AWS | S3 Bucket | example-corp-assets.s3.amazonaws.com | [Accessible / Denied] |
| Azure | Blob Storage | examplecorp.blob.core.windows.net | [Accessible / Denied] |
| GCP | Storage | storage.googleapis.com/example-corp | [Accessible / Denied] |

---

## 6. Email Addresses

**Total unique emails found**: [XX]

| Email Address | Source | In Breach Data? | Breaches |
|---------------|--------|-----------------|----------|
| admin@example.com | theHarvester | Yes | Collection #1, LinkedIn 2012 |
| dev@example.com | hunter.io | No | - |
| cto@example.com | LinkedIn | Yes | Adobe 2013 |

---

## 7. Technologies Identified

| Technology | Version | Source | Notes |
|------------|---------|--------|-------|
| nginx | 1.24.0 | Shodan | Web server |
| OpenSSH | 8.9 | Shodan | SSH access |
| PHP | 8.1 | Wayback URLs (.php) | Backend language |
| WordPress | 6.x | Shodan HTTP headers | CMS |
| AWS | - | LinkedIn job postings | Cloud provider |
| Kubernetes | - | LinkedIn job postings | Orchestration |

---

## 8. Email Security Posture

### 8.1 DNS Records

| Record Type | Value | Assessment |
|-------------|-------|------------|
| SPF | `v=spf1 include:_spf.google.com ~all` | Medium Risk - softfail |
| DMARC | `v=DMARC1; p=none; rua=mailto:dmarc@example.com` | Medium Risk - monitoring only |
| DKIM | `google` selector present | OK |
| MX | `aspmx.l.google.com` (priority 1) | Google Workspace |

### 8.2 Risk Assessment

| Finding | Risk Level | Recommendation |
|---------|-----------|----------------|
| SPF uses `~all` (softfail) | Medium | Change to `-all` (hardfail) |
| DMARC policy is `p=none` | Medium | Upgrade to `p=quarantine` then `p=reject` |
| DKIM configured | Low | Satisfactory |

---

## 9. Breach Data

| Breach Name | Date | Records | Data Types | Affected Emails |
|-------------|------|---------|------------|-----------------|
| Collection #1 | Jan 2019 | 773M | Emails, Passwords | admin@example.com |
| LinkedIn | Jun 2012 | 165M | Emails, Passwords | cto@example.com |

**Risk**: Credentials from these breaches may still be valid. Recommend enforcing password resets and MFA.

---

## 10. Code & Repository Findings

### 10.1 GitHub Organization

| Repository | Language | Last Updated | Notes |
|-----------|----------|-------------|-------|
| example-corp/webapp | Python | 2024-01-15 | Main web application |
| example-corp/infra | HCL | 2024-02-01 | Terraform infrastructure |
| example-corp/docs | Markdown | 2023-06-01 | Internal documentation |

### 10.2 Secrets Found

| Tool | Repository | Secret Type | Verified? | Commit | Author |
|------|-----------|-------------|-----------|--------|--------|
| TruffleHog | example-corp/webapp | AWS Access Key | Yes | abc1234 | dev@example.com |
| Gitleaks | example-corp/infra | Database Password | No | def5678 | ops@example.com |

---

## 11. Security Findings Summary

### 11.1 Findings by Severity

| Severity | Count |
|----------|-------|
| Critical | [X] |
| High | [X] |
| Medium | [X] |
| Low | [X] |
| Informational | [X] |

### 11.2 Detailed Findings

#### [CRITICAL] F-001: Live AWS Access Key in Public Repository

- **Asset**: github.com/example-corp/webapp
- **Description**: A valid AWS Access Key was found in commit `abc1234`. TruffleHog verified the key is still active.
- **Impact**: Full access to AWS resources associated with this key.
- **Recommendation**: Immediately rotate the key, audit CloudTrail for unauthorized usage, remove from git history.

#### [HIGH] F-002: Missing DMARC Enforcement

- **Asset**: example.com
- **Description**: DMARC policy is set to `p=none`, meaning spoofed emails are not blocked.
- **Impact**: Attackers can send emails appearing to come from @example.com for phishing.
- **Recommendation**: After monitoring DMARC reports, upgrade to `p=quarantine` then `p=reject`.

#### [MEDIUM] F-003: Typosquat Domains with MX Records

- **Asset**: examp1e.com, exampl3.com
- **Description**: [X] lookalike domains are registered and have MX records configured.
- **Impact**: These domains can receive email and may be used for phishing campaigns.
- **Recommendation**: Monitor these domains, consider acquiring them or filing takedown requests.

*(Continue for all findings...)*

---

## 12. Risk Scoring Matrix

| Severity | Criteria | Examples from This Assessment |
|----------|----------|-------------------------------|
| **Critical** | Live secrets, active exploits, direct access | F-001: Live AWS key |
| **High** | Missing security controls, breach exposure | F-002: No DMARC enforcement |
| **Medium** | Weak configurations, outdated software | F-003: Typosquat domains |
| **Low** | Informational, internal naming exposure | Staging subdomain names |

---

## 13. Recommendations

### Immediate Actions (Critical/High)
1. [ ] Rotate leaked AWS Access Key and audit CloudTrail logs
2. [ ] Enforce DMARC policy (`p=reject`)
3. [ ] Force password reset for all emails found in breach data
4. [ ] Enable MFA for all accounts

### Short-term Actions (Medium)
5. [ ] Harden SPF record to `-all`
6. [ ] Monitor/acquire typosquat domains
7. [ ] Update outdated software (nginx, OpenSSH)
8. [ ] Remove sensitive data from git history

### Long-term Actions (Low)
9. [ ] Implement continuous certificate transparency monitoring
10. [ ] Establish regular breach monitoring
11. [ ] Conduct full active assessment (see recommendations below)

---

## 14. Targets Prioritized for Active Phase

Based on passive findings, the following targets should be prioritized for active scanning:

| Priority | Target | Reason |
|----------|--------|--------|
| 1 | staging.example.com | Staging environments often have weaker controls |
| 2 | 203.0.113.11 | Multiple open ports, outdated software |
| 3 | api.example.com | API endpoint, potential for injection |
| 4 | jenkins.example.com | CI/CD system, build artifact exposure |

---

## Appendix A: Tool Output Summaries

### A.1 WHOIS Summary
```
[Paste relevant WHOIS output]
```

### A.2 Subdomain Discovery (Full List)
```
[Full subdomain list]
```

### A.3 Shodan Results
```
[Relevant Shodan output]
```

### A.4 theHarvester Output
```
[Relevant harvester output]
```

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| ASN | Autonomous System Number - identifies a network operator |
| CIDR | Classless Inter-Domain Routing - IP address range notation |
| DMARC | Domain-based Message Authentication, Reporting & Conformance |
| DKIM | DomainKeys Identified Mail |
| SPF | Sender Policy Framework |
| HIBP | Have I Been Pwned - breach database |
| CVE | Common Vulnerabilities and Exposures |
| OSINT | Open Source Intelligence |

---

*Report generated using RAVEN EASM Platform*
*Template version: 1.0*
