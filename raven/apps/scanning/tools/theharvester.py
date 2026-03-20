from .base import ToolRunner


class TheHarvesterRunner(ToolRunner):
    name = "theHarvester"
    timeout = 600

    def build_command(self, target, options=None):
        sources = "baidu,bing,crtsh,dnsdumpster,hackertarget,otx,rapiddns,urlscan"
        cmd = ["theHarvester", "-d", target, "-b", sources]
        return cmd

    def parse_output(self, raw_output):
        emails = []
        hosts = []
        section = None
        for line in raw_output.splitlines():
            line = line.strip()
            if "Emails found" in line:
                section = "emails"
            elif "Hosts found" in line:
                section = "hosts"
            elif line.startswith("[*]") or not line or line.startswith("-"):
                continue
            elif section == "emails" and "@" in line:
                emails.append(line)
            elif section == "hosts" and "." in line:
                hosts.append(line)
        return {"emails": emails, "hosts": hosts}
