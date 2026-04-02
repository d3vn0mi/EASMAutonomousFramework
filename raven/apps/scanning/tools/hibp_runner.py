import logging
from django.conf import settings
from .base import ToolRunner

logger = logging.getLogger(__name__)


class HIBPRunner(ToolRunner):
    name = "hibp"
    timeout = 120

    def build_command(self, target, options=None):
        return ["echo", "hibp-api-runner"]

    def parse_output(self, raw_output):
        return {}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        api_key = getattr(settings, "HIBP_API_KEY", "")
        if not api_key:
            return {"status": "failed", "error": "HIBP_API_KEY not configured"}

        try:
            import requests
            headers = {
                "hibp-api-key": api_key,
                "user-agent": "RAVEN-EASM",
            }
            is_email = "@" in target
            if is_email:
                url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}"
                params = {"truncateResponse": "false"}
            else:
                url = f"https://haveibeenpwned.com/api/v3/breaches"
                params = {"domain": target}

            resp = requests.get(url, headers=headers, params=params, timeout=30)

            if resp.status_code == 404:
                return {
                    "status": "completed",
                    "exit_code": 0,
                    "raw_output": "No breaches found",
                    "parsed": {"breaches": [], "count": 0},
                    "command": f"HIBP API: {target}",
                }

            resp.raise_for_status()
            data = resp.json()

            breaches = []
            for breach in data:
                breaches.append({
                    "name": breach.get("Name", ""),
                    "title": breach.get("Title", ""),
                    "domain": breach.get("Domain", ""),
                    "breach_date": breach.get("BreachDate", ""),
                    "pwn_count": breach.get("PwnCount", 0),
                    "data_classes": breach.get("DataClasses", []),
                    "is_verified": breach.get("IsVerified", False),
                })

            return {
                "status": "completed",
                "exit_code": 0,
                "raw_output": str(breaches)[:50000],
                "parsed": {"breaches": breaches, "count": len(breaches)},
                "command": f"HIBP API: {target}",
            }
        except Exception as e:
            logger.exception("HIBP query failed for %s", target)
            return {"status": "failed", "error": str(e)}
