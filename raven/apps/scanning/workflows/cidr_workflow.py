"""
CIDR Range Scan Workflow
Tier determines depth:
  - Bronze: masscan (fast port scan), nmap (service detection)
  - Silver: + shodan (passive enrichment), httpx, nuclei
  - Gold: + gowitness, whatweb
"""
from apps.scanning.tools.masscan_runner import MasscanRunner
from apps.scanning.tools.nmap_runner import NmapRunner
from apps.scanning.tools.nuclei_runner import NucleiRunner
from apps.scanning.tools.shodan_runner import ShodanRunner
from apps.scanning.tools.httpx_runner import HttpxRunner
from apps.scanning.tools.gowitness_runner import GoWitnessRunner
from apps.scanning.tools.whatweb_runner import WhatWebRunner


def get_cidr_tools(tier):
    """Return ordered list of (ToolRunner, options) for CIDR targets."""
    tools = [
        (MasscanRunner(), {"ports": "1-65535", "rate": "1000"}),
        (NmapRunner(), {"ports": "--top-ports 1000"}),
    ]

    if tier in ("silver", "gold"):
        tools.append((ShodanRunner(), {}))
        tools.append((HttpxRunner(), {}))
        tools.append((NucleiRunner(), {"severity": "critical,high,medium"}))
        tools[1] = (NmapRunner(), {"ports": "1-65535"})

    if tier == "gold":
        tools.append((GoWitnessRunner(), {}))
        tools.append((WhatWebRunner(), {}))

    return tools
