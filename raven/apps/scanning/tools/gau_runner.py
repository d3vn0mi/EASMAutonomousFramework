from .base import ToolRunner


class GauRunner(ToolRunner):
    name = "gau"
    timeout = 300

    def build_command(self, target, options=None):
        return ["gau", target]

    def parse_output(self, raw_output):
        urls = list({line.strip() for line in raw_output.splitlines() if line.strip()})
        return {"urls": sorted(urls), "count": len(urls)}
