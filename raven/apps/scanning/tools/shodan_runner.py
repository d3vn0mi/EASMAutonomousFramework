import logging
from django.conf import settings
from .base import ToolRunner

logger = logging.getLogger(__name__)


class ShodanRunner(ToolRunner):
    name = "shodan"
    timeout = 120

    def build_command(self, target, options=None):
        return ["echo", "shodan-api-runner"]

    def parse_output(self, raw_output):
        return {}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        api_key = getattr(settings, "SHODAN_API_KEY", "")
        if not api_key:
            return {"status": "failed", "error": "SHODAN_API_KEY not configured"}

        try:
            import shodan
            api = shodan.Shodan(api_key)

            is_ip = all(c in "0123456789." for c in target)
            if is_ip:
                result = api.host(target)
                ports = result.get("ports", [])
                vulns = result.get("vulns", [])
                banners = []
                for item in result.get("data", []):
                    banners.append({
                        "port": item.get("port"),
                        "transport": item.get("transport", "tcp"),
                        "product": item.get("product", ""),
                        "version": item.get("version", ""),
                        "banner": (item.get("data", ""))[:500],
                    })
                parsed = {
                    "ip": target,
                    "hostnames": result.get("hostnames", []),
                    "ports": ports,
                    "vulns": vulns,
                    "banners": banners,
                    "os": result.get("os"),
                    "org": result.get("org", ""),
                    "shodan_data": True,
                }
            else:
                results = api.search(f"hostname:{target}")
                hosts = []
                for match in results.get("matches", [])[:50]:
                    hosts.append({
                        "ip": match.get("ip_str", ""),
                        "port": match.get("port"),
                        "product": match.get("product", ""),
                        "version": match.get("version", ""),
                        "hostnames": match.get("hostnames", []),
                    })
                parsed = {
                    "hosts": hosts,
                    "total": results.get("total", 0),
                    "shodan_data": True,
                }

            return {
                "status": "completed",
                "exit_code": 0,
                "raw_output": str(parsed)[:50000],
                "parsed": parsed,
                "command": f"shodan.host({target})" if is_ip else f"shodan.search(hostname:{target})",
            }
        except Exception as e:
            logger.exception("Shodan query failed for %s", target)
            return {"status": "failed", "error": str(e)}
