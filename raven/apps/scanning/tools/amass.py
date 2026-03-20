from .base import ToolRunner


class AmassRunner(ToolRunner):
    name = "amass"
    timeout = 600

    def build_command(self, target, options=None):
        cmd = ["amass", "enum", "-passive", "-d", target]
        return cmd

    def parse_output(self, raw_output):
        subdomains = [line.strip() for line in raw_output.splitlines() if line.strip()]
        return {"subdomains": subdomains, "count": len(subdomains)}
