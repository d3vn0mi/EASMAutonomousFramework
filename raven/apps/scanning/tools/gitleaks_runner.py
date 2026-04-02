import json
from .base import ToolRunner


class GitleaksRunner(ToolRunner):
    name = "gitleaks"
    timeout = 600

    def build_command(self, target, options=None):
        return [
            "gitleaks", "detect",
            "--source", target,
            "--report-format", "json",
            "--report-path", "/dev/stdout",
        ]

    def validate_target(self, target):
        if not target or not target.strip():
            return False
        if target.startswith(("/", "http://", "https://", "git@")):
            return True
        return super().validate_target(target)

    def parse_output(self, raw_output):
        secrets = []
        try:
            data = json.loads(raw_output)
            if isinstance(data, list):
                for entry in data:
                    secrets.append({
                        "rule": entry.get("RuleID", ""),
                        "description": entry.get("Description", ""),
                        "file": entry.get("File", ""),
                        "commit": entry.get("Commit", ""),
                        "author": entry.get("Author", ""),
                        "email": entry.get("Email", ""),
                        "date": entry.get("Date", ""),
                    })
        except json.JSONDecodeError:
            pass
        return {"secrets": secrets, "count": len(secrets)}
