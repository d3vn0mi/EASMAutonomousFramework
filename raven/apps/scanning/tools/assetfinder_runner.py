from .base import ToolRunner


class AssetfinderRunner(ToolRunner):
    name = "assetfinder"
    timeout = 180

    def build_command(self, target, options=None):
        return ["assetfinder", "--subs-only", target]

    def parse_output(self, raw_output):
        subdomains = list({line.strip() for line in raw_output.splitlines() if line.strip()})
        return {"subdomains": sorted(subdomains), "count": len(subdomains)}
