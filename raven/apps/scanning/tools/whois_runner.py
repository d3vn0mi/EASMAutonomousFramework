import logging
from .base import ToolRunner

logger = logging.getLogger(__name__)


class WhoisRunner(ToolRunner):
    name = "whois"
    timeout = 120

    def build_command(self, target, options=None):
        return ["whois", target]

    def parse_output(self, raw_output):
        data = {
            "registrar": "",
            "creation_date": "",
            "expiration_date": "",
            "updated_date": "",
            "nameservers": [],
            "registrant_org": "",
            "registrant_country": "",
            "status": [],
        }
        for line in raw_output.splitlines():
            line = line.strip()
            lower = line.lower()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            value = value.strip()
            if not value:
                continue
            if "registrar" in lower and "url" not in lower and "abuse" not in lower and not data["registrar"]:
                data["registrar"] = value
            elif "creation date" in lower or "created" in lower:
                if not data["creation_date"]:
                    data["creation_date"] = value
            elif "expir" in lower:
                if not data["expiration_date"]:
                    data["expiration_date"] = value
            elif "updated date" in lower:
                if not data["updated_date"]:
                    data["updated_date"] = value
            elif "name server" in lower or "nserver" in lower:
                data["nameservers"].append(value.lower())
            elif "registrant organization" in lower or "registrant org" in lower:
                if not data["registrant_org"]:
                    data["registrant_org"] = value
            elif "registrant country" in lower:
                if not data["registrant_country"]:
                    data["registrant_country"] = value
            elif "status" in lower and "domain" in lower:
                data["status"].append(value)
        return {"whois_data": data}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        result = super().run(target, options, output_dir, stdin_input)
        if result.get("status") == "completed" and not result.get("parsed", {}).get("whois_data", {}).get("registrar"):
            try:
                import whois
                w = whois.whois(target)
                parsed = result.get("parsed", {})
                parsed["whois_data"].update({
                    "registrar": str(w.registrar or ""),
                    "creation_date": str(w.creation_date or ""),
                    "expiration_date": str(w.expiration_date or ""),
                    "nameservers": [str(ns).lower() for ns in (w.name_servers or [])],
                    "registrant_org": str(getattr(w, "org", "") or ""),
                    "registrant_country": str(getattr(w, "country", "") or ""),
                })
                result["parsed"] = parsed
            except Exception as e:
                logger.debug("python-whois fallback failed: %s", e)
        return result
