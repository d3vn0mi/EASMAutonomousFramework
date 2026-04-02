import json
import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("raven.audit")


class AuditTrailMiddleware(MiddlewareMixin):
    """Log state-changing requests for compliance audit trail."""

    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def process_response(self, request, response):
        if request.method not in self.AUDITED_METHODS:
            return response

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            log_entry = {
                "user": user.username,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "ip": self._get_client_ip(request),
            }
            logger.info(json.dumps(log_entry))

        return response

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
