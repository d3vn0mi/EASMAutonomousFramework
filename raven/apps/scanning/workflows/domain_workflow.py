"""
Domain Discovery Workflow
Implements the 7-stage RAVEN pipeline for domain-type scope items.
Tier determines depth:
  - Bronze: subfinder, amass, httpx, nmap (top 1000), nuclei
  - Silver: + theHarvester, waybackurls, gau, testssl, wafw00f, full port scan
  - Gold: + all Silver tools with extended options
"""
from apps.scanning.tools.subfinder import SubfinderRunner
from apps.scanning.tools.amass import AmassRunner
from apps.scanning.tools.httpx_runner import HttpxRunner
from apps.scanning.tools.nmap_runner import NmapRunner
from apps.scanning.tools.nuclei_runner import NucleiRunner
from apps.scanning.tools.theharvester import TheHarvesterRunner
from apps.scanning.tools.testssl_runner import TestsslRunner
from apps.scanning.tools.wafw00f_runner import Wafw00fRunner


def get_domain_tools(tier):
    """Return ordered list of (ToolRunner, options) for the given tier."""
    tools = [
        (SubfinderRunner(), {}),
        (AmassRunner(), {}),
        (HttpxRunner(), {}),
        (NmapRunner(), {"ports": "--top-ports 1000"}),
        (NucleiRunner(), {"severity": "critical,high,medium"}),
    ]

    if tier in ("silver", "gold"):
        tools.insert(2, (TheHarvesterRunner(), {}))
        tools.append((TestsslRunner(), {}))
        tools.append((Wafw00fRunner(), {}))
        # Upgrade nmap to full port scan for Silver/Gold
        for i, (tool, opts) in enumerate(tools):
            if tool.name == "nmap":
                tools[i] = (NmapRunner(), {"ports": "1-65535"})

    if tier == "gold":
        # Add extra severity levels for nuclei
        for i, (tool, opts) in enumerate(tools):
            if tool.name == "nuclei":
                tools[i] = (NucleiRunner(), {"severity": "critical,high,medium,low"})

    return tools
