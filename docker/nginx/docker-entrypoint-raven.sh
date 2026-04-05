#!/bin/sh
set -e

DOMAIN="${DOMAIN:-easm.ravensec.eu}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

# If no SSL certificate exists, generate a self-signed one so nginx can start
if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
    echo "No SSL certificate found for ${DOMAIN}. Generating self-signed certificate..."
    mkdir -p "${CERT_DIR}"
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "${CERT_DIR}/privkey.pem" \
        -out "${CERT_DIR}/fullchain.pem" \
        -subj "/CN=${DOMAIN}" 2>/dev/null
    echo "Self-signed certificate created. Replace with Let's Encrypt using:"
    echo "  docker compose exec nginx certbot --nginx -d ${DOMAIN}"
fi

# Hand off to the default nginx entrypoint
exec /docker-entrypoint.sh "$@"
