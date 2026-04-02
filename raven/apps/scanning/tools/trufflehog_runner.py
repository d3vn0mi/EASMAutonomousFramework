import json
from .base import ToolRunner


class TruffleHogRunner(ToolRunner):
    name = "trufflehog"
    timeout = 600

    def build_command(self, target, options=None):
        cmd = ["trufflehog", "git", target, "--json", "--only-verified"]
        if (options or {}).get("include_unverified"):
            cmd.remove("--only-verified")
        return cmd

    def validate_target(self, target):
        if not target or not target.strip():
            return False
        if target.startswith(("http://", "https://", "git@")):
            return True
        return super().validate_target(target)

    def parse_output(self, raw_output):
        secrets = []
        for line in raw_output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                secrets.append({
                    "detector": entry.get("DetectorName", entry.get("detectorName", "")),
                    "verified": entry.get("Verified", entry.get("verified", False)),
                    "source": entry.get("SourceMetadata", {}).get("Data", {}).get("Git", {}).get("repository", ""),
                    "file": entry.get("SourceMetadata", {}).get("Data", {}).get("Git", {}).get("file", ""),
                    "commit": entry.get("SourceMetadata", {}).get("Data", {}).get("Git", {}).get("commit", ""),
                })
            except json.JSONDecodeError:
                continue
        return {"secrets": secrets, "count": len(secrets)}
