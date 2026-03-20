import json
from .base import ToolRunner


class TestsslRunner(ToolRunner):
    name = "testssl"
    timeout = 600

    def build_command(self, target, options=None):
        cmd = ["testssl", "--jsonfile=-", "--warnings", "off", target]
        return cmd

    def parse_output(self, raw_output):
        try:
            data = json.loads(raw_output)
            return {"ssl_results": data}
        except json.JSONDecodeError:
            return {"raw": raw_output[:5000]}
