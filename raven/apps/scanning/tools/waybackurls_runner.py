from .base import ToolRunner


class WaybackUrlsRunner(ToolRunner):
    name = "waybackurls"
    timeout = 300

    def build_command(self, target, options=None):
        return ["waybackurls"]

    def run(self, target, options=None, output_dir=None, stdin_input=None):
        return super().run(target, options, output_dir, stdin_input=target + "\n")

    def parse_output(self, raw_output):
        urls = list({line.strip() for line in raw_output.splitlines() if line.strip()})
        return {"urls": sorted(urls), "count": len(urls)}
