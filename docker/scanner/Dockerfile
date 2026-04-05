###############################################################################
# RAVEN EASM Scanner Worker
# Adapted from documentation/Dockerfile — all recon tools, no Kasm desktop.
# Runs as a Celery worker consuming from the 'scanning' queue.
###############################################################################

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOPATH=/opt/go \
    PATH="/opt/go/bin:/usr/local/go/bin:${PATH}"

WORKDIR /app

# ── System packages & build deps ─────────────────────────────────────────
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
    masscan \
    libnet-ssleay-perl \
    chromium \
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
    sslscan \
    dirb \
    whatweb \
    && rm -rf /var/lib/apt/lists/*

# ── Nikto (from source — not in Debian Trixie repos) ────────────────────
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

# ── Go 1.22 ──────────────────────────────────────────────────────────────
RUN curl -sSL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz | tar -C /usr/local -xz \
    && mkdir -p ${GOPATH}/{bin,src}

# ── Release Binaries ─────────────────────────────────────────────────────
RUN AMASS_VER="v4.2.0" \
    && curl -sSL "https://github.com/owasp-amass/amass/releases/download/${AMASS_VER}/amass_Linux_amd64.zip" \
       -o /tmp/amass.zip \
    && unzip -j /tmp/amass.zip "*/amass" -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/amass \
    && rm /tmp/amass.zip

RUN NUCLEI_VER="v3.3.7" \
    && curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/${NUCLEI_VER}/nuclei_${NUCLEI_VER#v}_linux_amd64.zip" \
       -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip

RUN SUBFINDER_VER="v2.6.7" \
    && curl -sSL "https://github.com/projectdiscovery/subfinder/releases/download/${SUBFINDER_VER}/subfinder_${SUBFINDER_VER#v}_linux_amd64.zip" \
       -o /tmp/subfinder.zip \
    && unzip -o /tmp/subfinder.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/subfinder \
    && rm /tmp/subfinder.zip

RUN HTTPX_VER="v1.6.10" \
    && curl -sSL "https://github.com/projectdiscovery/httpx/releases/download/${HTTPX_VER}/httpx_${HTTPX_VER#v}_linux_amd64.zip" \
       -o /tmp/httpx.zip \
    && unzip -o /tmp/httpx.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/httpx \
    && rm /tmp/httpx.zip

RUN DNSX_VER="v1.2.1" \
    && curl -sSL "https://github.com/projectdiscovery/dnsx/releases/download/${DNSX_VER}/dnsx_${DNSX_VER#v}_linux_amd64.zip" \
       -o /tmp/dnsx.zip \
    && unzip -o /tmp/dnsx.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/dnsx \
    && rm /tmp/dnsx.zip

RUN FEROX_VER="v2.11.0" \
    && curl -sSL "https://github.com/epi052/feroxbuster/releases/download/${FEROX_VER}/x86_64-linux-feroxbuster.zip" \
       -o /tmp/ferox.zip \
    && unzip -o /tmp/ferox.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/feroxbuster \
    && rm /tmp/ferox.zip

RUN TRUFFLEHOG_VER="3.82.13" \
    && curl -sSL "https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VER}/trufflehog_${TRUFFLEHOG_VER}_linux_amd64.tar.gz" \
       | tar -xz -C /usr/local/bin/ trufflehog \
    && chmod +x /usr/local/bin/trufflehog

# ── Go-installed tools ───────────────────────────────────────────────────
RUN go install -v github.com/tomnomnom/assetfinder@latest \
    && go install -v github.com/tomnomnom/waybackurls@latest \
    && go install -v github.com/lc/gau/v2/cmd/gau@latest \
    && go install -v github.com/sensepost/gowitness@latest \
    && go install -v github.com/ffuf/ffuf/v2@latest \
    && go install -v github.com/haccer/subjack@latest \
    && go install -v github.com/gitleaks/gitleaks/v8/cmd/gitleaks@latest

RUN go install -v github.com/d3mondev/puredns/v2@latest || true

# ── Python recon tools ───────────────────────────────────────────────────
RUN pip install --no-cache-dir \
    theHarvester \
    shodan \
    censys \
    recon-ng \
    dnstwist \
    fierce \
    wafw00f \
    dirsearch \
    arjun

# ── testssl.sh ────────────────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl.sh \
    && ln -s /opt/testssl.sh/testssl.sh /usr/local/bin/testssl

# ── Nuclei templates ─────────────────────────────────────────────────────
RUN nuclei -update-templates 2>/dev/null || true

# ── SecLists wordlists ───────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/danielmiessler/SecLists.git /opt/seclists

# ── Python app dependencies (Django + Celery) ────────────────────────────
COPY requirements/scanner.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY raven/ /app/

CMD ["celery", "-A", "raven", "worker", "-Q", "scanning", "-l", "info", "--concurrency=2"]
