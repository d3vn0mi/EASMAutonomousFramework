###############################################################################
# RAVEN EASM Workspace — Kasm-compatible Docker image
# All tools referenced in the RAVEN EASM Service Guide (Bronze/Silver/Gold)
#
# Build:  docker build -t raven-easm:latest .
# Kasm:   Import as a custom workspace image in Kasm admin panel
###############################################################################

FROM kasmweb/core-ubuntu-jammy:1.16.1
USER root

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/kasm-default-profile \
    STARTUPDIR=/dockerstartup \
    GOPATH=/opt/go \
    PATH="/opt/go/bin:/usr/local/go/bin:/home/kasm-default-profile/.local/bin:${PATH}"

# ─── System packages & build deps ───────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    jq \
    dnsutils \
    whois \
    nmap \
    nikto \
    masscan \
    chromium-browser \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpcap-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    net-tools \
    iputils-ping \
    traceroute \
    tcpdump \
    netcat-openbsd \
    sslscan \
    wfuzz \
    dirb \
    whatweb \
    ruby \
    ruby-dev \
    && rm -rf /var/lib/apt/lists/*

# ─── Go 1.22 ────────────────────────────────────────────────────────────────
RUN curl -sSL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz | tar -C /usr/local -xz \
    && mkdir -p ${GOPATH}/{bin,src}

# ═══════════════════════════════════════════════════════════════════════════
#  RELEASE BINARIES — tools that are large to compile or not written in Go
# ═══════════════════════════════════════════════════════════════════════════

# Amass v4 — release binary (compiling the full repo is unreliable)
RUN AMASS_VER="v4.2.0" \
    && curl -sSL "https://github.com/owasp-amass/amass/releases/download/${AMASS_VER}/amass_Linux_amd64.zip" \
       -o /tmp/amass.zip \
    && unzip -j /tmp/amass.zip "*/amass" -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/amass \
    && rm /tmp/amass.zip

# Feroxbuster — written in Rust, install pre-built binary
RUN FEROX_VER="v2.11.0" \
    && curl -sSL "https://github.com/epi052/feroxbuster/releases/download/${FEROX_VER}/x86_64-linux-feroxbuster.zip" \
       -o /tmp/ferox.zip \
    && unzip /tmp/ferox.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/feroxbuster \
    && rm /tmp/ferox.zip

# TruffleHog v3 — very heavy Go build, use release binary
RUN TRUFFLEHOG_VER="3.82.13" \
    && curl -sSL "https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VER}/trufflehog_${TRUFFLEHOG_VER}_linux_amd64.tar.gz" \
       | tar -xz -C /usr/local/bin/ trufflehog \
    && chmod +x /usr/local/bin/trufflehog

# Nuclei — release binary for speed
RUN NUCLEI_VER="v3.3.7" \
    && curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/${NUCLEI_VER}/nuclei_${NUCLEI_VER#v}_linux_amd64.zip" \
       -o /tmp/nuclei.zip \
    && unzip /tmp/nuclei.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip

# Subfinder — release binary
RUN SUBFINDER_VER="v2.6.7" \
    && curl -sSL "https://github.com/projectdiscovery/subfinder/releases/download/${SUBFINDER_VER}/subfinder_${SUBFINDER_VER#v}_linux_amd64.zip" \
       -o /tmp/subfinder.zip \
    && unzip /tmp/subfinder.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/subfinder \
    && rm /tmp/subfinder.zip

# httpx — release binary
RUN HTTPX_VER="v1.6.10" \
    && curl -sSL "https://github.com/projectdiscovery/httpx/releases/download/${HTTPX_VER}/httpx_${HTTPX_VER#v}_linux_amd64.zip" \
       -o /tmp/httpx.zip \
    && unzip /tmp/httpx.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/httpx \
    && rm /tmp/httpx.zip

# dnsx — release binary
RUN DNSX_VER="v1.2.1" \
    && curl -sSL "https://github.com/projectdiscovery/dnsx/releases/download/${DNSX_VER}/dnsx_${DNSX_VER#v}_linux_amd64.zip" \
       -o /tmp/dnsx.zip \
    && unzip /tmp/dnsx.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/dnsx \
    && rm /tmp/dnsx.zip

# ═══════════════════════════════════════════════════════════════════════════
#  GO INSTALL — lighter tools that compile quickly and reliably
# ═══════════════════════════════════════════════════════════════════════════

# Discovery
RUN go install -v github.com/tomnomnom/assetfinder@latest
RUN go install -v github.com/tomnomnom/waybackurls@latest
RUN go install -v github.com/lc/gau/v2/cmd/gau@latest

# Enumeration
RUN go install -v github.com/sensepost/gowitness@latest
RUN go install -v github.com/ffuf/ffuf/v2@latest

# Vulnerability / recon
RUN go install -v github.com/haccer/subjack@latest
RUN go install -v github.com/gitleaks/gitleaks/v8/cmd/gitleaks@latest

# Optional extras (non-fatal if they fail)
RUN go install -v github.com/d3mondev/puredns/v2@latest || true

# ═══════════════════════════════════════════════════════════════════════════
#  PYTHON TOOLS
# ═══════════════════════════════════════════════════════════════════════════

RUN pip3 install --break-system-packages --no-cache-dir \
    theHarvester \
    shodan \
    censys \
    spiderfoot \
    recon-ng \
    dnstwist \
    scoutsuite \
    fierce \
    wafw00f \
    dirsearch \
    arjun

RUN pip3 install --break-system-packages --no-cache-dir \
    requests \
    beautifulsoup4 \
    python-whois \
    dnspython \
    paramiko \
    netaddr \
    python-nmap \
    jinja2 \
    pyyaml \
    rich \
    tabulate

# ─── testssl.sh ─────────────────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl.sh \
    && ln -s /opt/testssl.sh/testssl.sh /usr/local/bin/testssl

# ─── SecLists wordlists ────────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/danielmiessler/SecLists.git /opt/seclists

# ─── Nuclei templates ──────────────────────────────────────────────────────
RUN nuclei -update-templates 2>/dev/null || true

# ─── Reporting & utility packages ──────────────────────────────────────────
RUN pip3 install --break-system-packages --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    markdown \
    weasyprint \
    matplotlib \
    pandas

# ═══════════════════════════════════════════════════════════════════════════
#  RAVEN WRAPPER SCRIPTS
# ═══════════════════════════════════════════════════════════════════════════

RUN mkdir -p /opt/raven/bin /opt/raven/templates /opt/raven/output

COPY <<'RAVEN_SCAN' /opt/raven/bin/raven-quick-scan
#!/usr/bin/env bash
# RAVEN Quick Scan — runs the Bronze-tier discovery pipeline on a target domain
set -euo pipefail
DOMAIN="${1:?Usage: raven-quick-scan <domain>}"
OUT="/opt/raven/output/${DOMAIN}_$(date +%Y%m%d_%H%M)"
mkdir -p "$OUT"

echo "[*] RAVEN EASM — Quick Scan for: $DOMAIN"
echo "[*] Output: $OUT"
echo ""

echo "[1/6] Subfinder — passive subdomain enumeration"
subfinder -d "$DOMAIN" -silent -o "$OUT/subdomains_subfinder.txt" 2>/dev/null

echo "[2/6] Amass — comprehensive enumeration"
timeout 300 amass enum -passive -d "$DOMAIN" -o "$OUT/subdomains_amass.txt" 2>/dev/null || true

echo "[3/6] Merging & deduplicating subdomains"
cat "$OUT"/subdomains_*.txt 2>/dev/null | sort -u > "$OUT/all_subdomains.txt"
echo "    Found $(wc -l < "$OUT/all_subdomains.txt") unique subdomains"

echo "[4/6] httpx — probing live hosts"
httpx -l "$OUT/all_subdomains.txt" -silent -status-code -title -tech-detect \
    -o "$OUT/live_hosts.txt" 2>/dev/null || true

echo "[5/6] Nmap — top 1000 port scan on live hosts"
awk '{print $1}' "$OUT/live_hosts.txt" 2>/dev/null | \
    sed 's|https\?://||;s|/.*||;s|:.*||' | sort -u > "$OUT/targets_for_nmap.txt"
nmap -iL "$OUT/targets_for_nmap.txt" -T4 --top-ports 1000 -oN "$OUT/nmap_results.txt" 2>/dev/null || true

echo "[6/6] Nuclei — template-based vulnerability scan"
nuclei -l "$OUT/live_hosts.txt" -severity critical,high,medium \
    -o "$OUT/nuclei_findings.txt" 2>/dev/null || true

echo ""
echo "[✓] Scan complete. Results in: $OUT"
echo "    Subdomains:  $OUT/all_subdomains.txt"
echo "    Live hosts:  $OUT/live_hosts.txt"
echo "    Ports:       $OUT/nmap_results.txt"
echo "    Vulns:       $OUT/nuclei_findings.txt"
RAVEN_SCAN

COPY <<'RAVEN_FULL' /opt/raven/bin/raven-full-scan
#!/usr/bin/env bash
# RAVEN Full Scan — Silver/Gold tier pipeline
set -euo pipefail
DOMAIN="${1:?Usage: raven-full-scan <domain>}"
OUT="/opt/raven/output/${DOMAIN}_full_$(date +%Y%m%d_%H%M)"
mkdir -p "$OUT"

echo "[*] RAVEN EASM — Full Assessment for: $DOMAIN"
echo "[*] Output: $OUT"
echo ""

# ── Discovery ──
echo "=== PHASE 1: Asset Discovery ==="
subfinder -d "$DOMAIN" -all -silent -o "$OUT/subs_subfinder.txt" 2>/dev/null
timeout 600 amass enum -d "$DOMAIN" -o "$OUT/subs_amass.txt" 2>/dev/null || true
theHarvester -d "$DOMAIN" -b all -f "$OUT/theharvester" 2>/dev/null || true
echo "$DOMAIN" | waybackurls > "$OUT/wayback_urls.txt" 2>/dev/null || true
echo "$DOMAIN" | gau --threads 5 > "$OUT/gau_urls.txt" 2>/dev/null || true

cat "$OUT"/subs_*.txt 2>/dev/null | sort -u > "$OUT/all_subdomains.txt"
echo "    Subdomains: $(wc -l < "$OUT/all_subdomains.txt")"

# ── Enumeration ──
echo ""
echo "=== PHASE 2: Enumeration ==="
httpx -l "$OUT/all_subdomains.txt" -silent -status-code -title -tech-detect \
    -follow-redirects -o "$OUT/live_hosts.txt" 2>/dev/null || true

awk '{print $1}' "$OUT/live_hosts.txt" | sed 's|https\?://||;s|/.*||;s|:.*||' | \
    sort -u > "$OUT/ip_targets.txt"

echo "[*] Full TCP port scan (all 65535)"
nmap -iL "$OUT/ip_targets.txt" -p- -T4 -sV --open -oN "$OUT/nmap_full.txt" 2>/dev/null || true

echo "[*] SSL/TLS analysis"
while read -r host; do
    testssl --quiet --csv "$host" >> "$OUT/testssl_results.csv" 2>/dev/null || true
done < <(head -20 "$OUT/ip_targets.txt")

echo "[*] WAF detection"
wafw00f -i "$OUT/live_hosts.txt" -o "$OUT/waf_results.txt" 2>/dev/null || true

echo "[*] Screenshots"
gowitness file -f "$OUT/live_hosts.txt" --screenshot-path "$OUT/screenshots/" 2>/dev/null || true

# ── Vulnerability Assessment ──
echo ""
echo "=== PHASE 3: Vulnerability Assessment ==="
nuclei -l "$OUT/live_hosts.txt" -severity critical,high,medium,low \
    -o "$OUT/nuclei_all.txt" 2>/dev/null || true

echo "[*] Subdomain takeover check"
subjack -w "$OUT/all_subdomains.txt" -t 50 -timeout 30 -ssl \
    -o "$OUT/takeover_results.txt" 2>/dev/null || true

echo "[*] DNS security checks (SPF/DKIM/DMARC)"
dig +short "$DOMAIN" TXT > "$OUT/dns_txt.txt" 2>/dev/null
dig +short "_dmarc.$DOMAIN" TXT >> "$OUT/dns_txt.txt" 2>/dev/null

echo "[*] Secret scanning on discovered URLs"
cat "$OUT/wayback_urls.txt" "$OUT/gau_urls.txt" 2>/dev/null | sort -u | \
    grep -iE '\.(json|yml|yaml|xml|conf|cfg|env|sql|bak|old|log)$' > "$OUT/interesting_urls.txt" || true

echo ""
echo "[✓] Full assessment complete. Results: $OUT/"
ls -la "$OUT/"
RAVEN_FULL

RUN chmod +x /opt/raven/bin/* \
    && ln -s /opt/raven/bin/raven-quick-scan /usr/local/bin/raven-quick-scan \
    && ln -s /opt/raven/bin/raven-full-scan  /usr/local/bin/raven-full-scan

# ─── Desktop shortcut (Kasm) ───────────────────────────────────────────────
COPY <<'DESKTOP' /home/kasm-default-profile/Desktop/RAVEN-Terminal.desktop
[Desktop Entry]
Type=Application
Name=RAVEN Terminal
Exec=bash -c 'echo "=== RAVEN EASM Workspace ===" && echo "" && echo "Quick scan:  raven-quick-scan <domain>" && echo "Full scan:   raven-full-scan <domain>" && echo "" && echo "Tools: amass, subfinder, nmap, masscan, nuclei, httpx," && echo "       nikto, ffuf, testssl, gowitness, gitleaks, ..." && echo "" && echo "Wordlists:   /opt/seclists/" && echo "Output dir:  /opt/raven/output/" && echo "" && exec bash'
Icon=utilities-terminal
Terminal=true
DESKTOP

# ─── MOTD ───────────────────────────────────────────────────────────────────
COPY <<'MOTD' /etc/motd

╔══════════════════════════════════════════════════════════════╗
║           RAVEN Cybersecurity IKE — EASM Workspace          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  DISCOVERY         ENUMERATION        VULNERABILITY          ║
║  ─────────         ───────────        ─────────────          ║
║  amass             nmap               nuclei                 ║
║  subfinder         masscan            nikto                  ║
║  theHarvester      httpx              subjack                ║
║  assetfinder       gowitness          gitleaks               ║
║  waybackurls       whatweb            trufflehog             ║
║  gau               testssl            scoutsuite             ║
║  recon-ng          ffuf               wafw00f                ║
║  spiderfoot        feroxbuster        dnstwist               ║
║  dnsx              sslscan            dirsearch              ║
║                                                              ║
║  QUICK COMMANDS                                              ║
║  ──────────────                                              ║
║  raven-quick-scan <domain>    Bronze-tier auto pipeline      ║
║  raven-full-scan  <domain>    Silver/Gold full assessment    ║
║                                                              ║
║  Wordlists: /opt/seclists/                                   ║
║  Output:    /opt/raven/output/                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

MOTD

RUN echo 'cat /etc/motd' >> /home/kasm-default-profile/.bashrc

# ─── Fix permissions for Kasm default user ──────────────────────────────────
RUN chown -R 1000:1000 /opt/raven /home/kasm-default-profile \
    && chown -R 1000:1000 ${GOPATH} || true

USER 1000

LABEL maintainer="RAVEN Cybersecurity IKE" \
      description="RAVEN EASM assessment workspace for Kasm — all tiers" \
      version="1.0"
