import json
from .base import ToolRunner


class DnsxRunner(ToolRunner):
    name = "dnsx"
    timeout = 300

    def build_command(self, target, options=None):
        cmd = ["dnsx", "-d", target, "-resp", "-json", "-silent"]
        return cmd

    def parse_output(self, raw_output):
        records = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    records.append({"raw": line})
        return {"dns_records": records, "count": len(records)}
