FROM nginx:1.27-alpine

RUN apk add --no-cache certbot certbot-nginx openssl

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint-raven.sh /docker-entrypoint-raven.sh
RUN chmod +x /docker-entrypoint-raven.sh

EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint-raven.sh"]
CMD ["nginx", "-g", "daemon off;"]
