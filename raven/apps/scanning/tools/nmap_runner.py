import re
from .base import ToolRunner


class NmapRunner(ToolRunner):
    name = "nmap"
    timeout = 1800

    def build_command(self, target, options=None):
        options = options or {}
        ports = options.get("ports", "--top-ports 1000")
        cmd = ["nmap", "-T4", target]
        if ports.startswith("--"):
            cmd.append(ports)
        else:
            cmd.extend(["-p", ports])
        cmd.extend(["-sV", "--open"])
        return cmd

    def parse_output(self, raw_output):
        open_ports = []
        for line in raw_output.splitlines():
            match = re.match(r"(\d+)/(tcp|udp)\s+open\s+(\S+)\s*(.*)", line)
            if match:
                open_ports.append({
                    "port": int(match.group(1)),
                    "protocol": match.group(2),
                    "service": match.group(3),
                    "version": match.group(4).strip(),
                })
        return {"open_ports": open_ports, "count": len(open_ports)}
