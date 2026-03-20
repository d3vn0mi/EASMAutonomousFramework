"""
IP/CIDR Scan Workflow
"""
from apps.scanning.tools.nmap_runner import NmapRunner
from apps.scanning.tools.masscan_runner import MasscanRunner
from apps.scanning.tools.nuclei_runner import NucleiRunner


def get_ip_tools(tier):
    """Return ordered list of (ToolRunner, options) for IP/CIDR targets."""
    tools = [
        (NmapRunner(), {"ports": "--top-ports 1000"}),
        (NucleiRunner(), {"severity": "critical,high,medium"}),
    ]

    if tier in ("silver", "gold"):
        tools.insert(0, (MasscanRunner(), {"ports": "1-65535", "rate": "1000"}))
        tools[1] = (NmapRunner(), {"ports": "1-65535"})

    return tools
