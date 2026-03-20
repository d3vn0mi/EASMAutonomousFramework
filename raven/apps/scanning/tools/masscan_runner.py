import json
from .base import ToolRunner


class MasscanRunner(ToolRunner):
    name = "masscan"
    timeout = 1200

    def build_command(self, target, options=None):
        options = options or {}
        ports = options.get("ports", "1-65535")
        rate = options.get("rate", "1000")
        cmd = ["masscan", target, "-p", ports, "--rate", str(rate), "-oJ", "-"]
        return cmd

    def parse_output(self, raw_output):
        results = []
        try:
            # masscan JSON output can have trailing commas
            cleaned = raw_output.strip().rstrip(",")
            if cleaned and not cleaned.startswith("["):
                cleaned = "[" + cleaned + "]"
            if cleaned:
                results = json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        return {"hosts": results, "count": len(results)}
