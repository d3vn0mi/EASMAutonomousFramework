from .base import ToolRunner


class SubfinderRunner(ToolRunner):
    name = "subfinder"
    timeout = 300

    def build_command(self, target, options=None):
        cmd = ["subfinder", "-d", target, "-silent"]
        if options and options.get("recursive"):
            cmd.append("-recursive")
        return cmd

    def parse_output(self, raw_output):
        subdomains = [line.strip() for line in raw_output.splitlines() if line.strip()]
        return {"subdomains": subdomains, "count": len(subdomains)}
