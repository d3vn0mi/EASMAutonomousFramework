import json
import logging
from .base import ToolRunner

logger = logging.getLogger(__name__)


class CrtshRunner(ToolRunner):
    name = "crtsh"
    timeout = 120

    def build_command(self, target, options=None):
        return ["echo", "crtsh-api-runner"]

    def parse_output(self, raw_output):
        return {}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        try:
            import requests
            url = f"https://crt.sh/?q=%.{target}&output=json"
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            seen = set()
            subdomains = []
            certificates = []
            for entry in data:
                cn = entry.get("common_name", "").strip().lower()
                name_value = entry.get("name_value", "")
                cert_info = {
                    "id": entry.get("id"),
                    "issuer": entry.get("issuer_name", ""),
                    "common_name": cn,
                    "not_before": entry.get("not_before", ""),
                    "not_after": entry.get("not_after", ""),
                }
                certificates.append(cert_info)

                for name in name_value.split("\n"):
                    name = name.strip().lower()
                    if name and name not in seen and not name.startswith("*"):
                        seen.add(name)
                        subdomains.append(name)

            return {
                "status": "completed",
                "exit_code": 0,
                "raw_output": json.dumps({"total_certs": len(data), "subdomains_found": len(subdomains)})[:50000],
                "parsed": {
                    "subdomains": sorted(subdomains),
                    "certificates": certificates[:100],
                    "count": len(subdomains),
                },
                "command": f"crt.sh/?q=%.{target}",
            }
        except Exception as e:
            logger.exception("crt.sh query failed for %s", target)
            return {"status": "failed", "error": str(e)}
