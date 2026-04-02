import json
from .base import ToolRunner


class NucleiRunner(ToolRunner):
    name = "nuclei"
    timeout = 1800

    def build_command(self, target, options=None):
        options = options or {}
        severity = options.get("severity", "critical,high,medium")
        cmd = ["nuclei", "-u", target, "-severity", severity, "-jsonl", "-silent"]
        return cmd

    def parse_output(self, raw_output):
        findings = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line:
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    findings.append({"raw": line})
        return {"findings": findings, "count": len(findings)}
