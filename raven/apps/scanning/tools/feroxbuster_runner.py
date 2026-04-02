import json
from .base import ToolRunner


class FeroxbusterRunner(ToolRunner):
    name = "feroxbuster"
    timeout = 1200

    def build_command(self, target, options=None):
        url = target if target.startswith("http") else f"https://{target}"
        wordlist = (options or {}).get(
            "wordlist", "/opt/seclists/Discovery/Web-Content/common.txt"
        )
        cmd = [
            "feroxbuster", "-u", url,
            "--json", "--silent",
            "-w", wordlist,
        ]
        if (options or {}).get("depth"):
            cmd.extend(["-d", str(options["depth"])])
        return cmd

    def parse_output(self, raw_output):
        paths = []
        for line in raw_output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "response":
                    paths.append({
                        "url": entry.get("url", ""),
                        "status": entry.get("status", 0),
                        "content_length": entry.get("content_length", 0),
                        "lines": entry.get("line_count", 0),
                        "words": entry.get("word_count", 0),
                    })
            except json.JSONDecodeError:
                continue
        return {"paths": paths, "count": len(paths)}
