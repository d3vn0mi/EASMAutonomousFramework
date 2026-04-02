import json
from .base import ToolRunner


class DnstwistRunner(ToolRunner):
    name = "dnstwist"
    timeout = 600

    def build_command(self, target, options=None):
        return ["dnstwist", "--format", "json", target]

    def parse_output(self, raw_output):
        permutations = []
        try:
            data = json.loads(raw_output)
            if isinstance(data, list):
                for entry in data:
                    perm = {
                        "domain": entry.get("domain", ""),
                        "fuzzer": entry.get("fuzzer", ""),
                    }
                    if entry.get("dns_a"):
                        perm["dns_a"] = entry["dns_a"]
                    if entry.get("dns_mx"):
                        perm["dns_mx"] = entry["dns_mx"]
                    if entry.get("dns_ns"):
                        perm["dns_ns"] = entry["dns_ns"]
                    permutations.append(perm)
        except json.JSONDecodeError:
            pass
        return {"permutations": permutations, "count": len(permutations)}
