import os
import tempfile
from .base import ToolRunner


class GoWitnessRunner(ToolRunner):
    name = "gowitness"
    timeout = 600

    def build_command(self, target, options=None):
        output_dir = (options or {}).get("output_dir", "/tmp/gowitness")
        chrome_path = (options or {}).get("chrome_path", "/usr/bin/chromium")
        url = target if target.startswith("http") else f"https://{target}"
        return [
            "gowitness", "single", url,
            "--screenshot-path", output_dir,
            "--chrome-path", chrome_path,
        ]

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        options = options or {}
        if "output_dir" not in options:
            options["output_dir"] = tempfile.mkdtemp(prefix="gowitness_")
        return super().run(target, options, output_dir, stdin_input)

    def parse_output(self, raw_output):
        screenshot_files = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line.endswith(".png") or line.endswith(".jpg"):
                screenshot_files.append(line)
        return {"screenshots": screenshot_files, "count": len(screenshot_files)}
