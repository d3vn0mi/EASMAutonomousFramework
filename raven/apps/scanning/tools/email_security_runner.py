import logging
from .base import ToolRunner

logger = logging.getLogger(__name__)


class EmailSecurityRunner(ToolRunner):
    name = "email_security"
    timeout = 120

    def build_command(self, target, options=None):
        return ["echo", "email-security-runner"]

    def parse_output(self, raw_output):
        return {}

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        if not self.validate_target(target):
            return {"error": f"Invalid target: {target}", "status": "failed"}

        # Extract domain from email if needed
        domain = target.split("@")[-1] if "@" in target else target

        try:
            import dns.resolver

            resolver = dns.resolver.Resolver()
            resolver.timeout = 10
            resolver.lifetime = 10

            # SPF check
            spf = {"exists": False, "record": "", "policy": ""}
            try:
                answers = resolver.resolve(domain, "TXT")
                for rdata in answers:
                    txt = rdata.to_text().strip('"')
                    if txt.startswith("v=spf1"):
                        spf["exists"] = True
                        spf["record"] = txt
                        if "-all" in txt:
                            spf["policy"] = "hard_fail"
                        elif "~all" in txt:
                            spf["policy"] = "soft_fail"
                        elif "?all" in txt:
                            spf["policy"] = "neutral"
                        elif "+all" in txt:
                            spf["policy"] = "pass_all"
                        break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                pass

            # DMARC check
            dmarc = {"exists": False, "record": "", "policy": ""}
            try:
                answers = resolver.resolve(f"_dmarc.{domain}", "TXT")
                for rdata in answers:
                    txt = rdata.to_text().strip('"')
                    if txt.startswith("v=DMARC1"):
                        dmarc["exists"] = True
                        dmarc["record"] = txt
                        for part in txt.split(";"):
                            part = part.strip()
                            if part.startswith("p="):
                                dmarc["policy"] = part[2:]
                        break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                pass

            # DKIM check (common selectors)
            dkim = {"exists": False, "selectors_found": []}
            for selector in ["default", "google", "selector1", "selector2", "k1", "mail", "dkim"]:
                try:
                    answers = resolver.resolve(f"{selector}._domainkey.{domain}", "TXT")
                    for rdata in answers:
                        txt = rdata.to_text().strip('"')
                        if "v=DKIM1" in txt or "k=rsa" in txt:
                            dkim["exists"] = True
                            dkim["selectors_found"].append(selector)
                            break
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    continue

            # MX records
            mx_records = []
            try:
                answers = resolver.resolve(domain, "MX")
                for rdata in answers:
                    mx_records.append({
                        "priority": rdata.preference,
                        "server": str(rdata.exchange).rstrip("."),
                    })
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                pass

            # Determine spoofability
            spoofable = not (spf["exists"] and dmarc["exists"] and dmarc["policy"] in ("reject", "quarantine"))

            parsed = {
                "domain": domain,
                "spf": spf,
                "dmarc": dmarc,
                "dkim": dkim,
                "mx_records": mx_records,
                "spoofable": spoofable,
            }

            return {
                "status": "completed",
                "exit_code": 0,
                "raw_output": str(parsed)[:50000],
                "parsed": parsed,
                "command": f"DNS email security check: {domain}",
            }
        except Exception as e:
            logger.exception("Email security check failed for %s", target)
            return {"status": "failed", "error": str(e)}
