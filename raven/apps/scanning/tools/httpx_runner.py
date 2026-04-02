import json
from .base import ToolRunner


class HttpxRunner(ToolRunner):
    name = "httpx"
    timeout = 600

    def build_command(self, target, options=None):
        cmd = ["httpx", "-u", target, "-silent", "-status-code", "-title",
               "-tech-detect", "-json"]
        return cmd

    def parse_output(self, raw_output):
        results = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    results.append({"raw": line})
        return {"hosts": results, "count": len(results)}
