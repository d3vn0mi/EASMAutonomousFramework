"""
Domain Discovery Workflow
Implements the multi-stage RAVEN pipeline for domain-type scope items.
Tier determines depth:
  - Bronze: subfinder, amass, assetfinder, crtsh, httpx, nmap (top 1000), nuclei, whois
  - Silver: + theHarvester, whatweb, gowitness, testssl, wafw00f, waybackurls, gau,
            dnstwist, shodan, full port scan
  - Gold: + feroxbuster, nuclei all severities
"""
from apps.scanning.tools.subfinder import SubfinderRunner
from apps.scanning.tools.amass import AmassRunner
from apps.scanning.tools.assetfinder_runner import AssetfinderRunner
from apps.scanning.tools.crtsh_runner import CrtshRunner
from apps.scanning.tools.httpx_runner import HttpxRunner
from apps.scanning.tools.nmap_runner import NmapRunner
from apps.scanning.tools.nuclei_runner import NucleiRunner
from apps.scanning.tools.whois_runner import WhoisRunner
from apps.scanning.tools.theharvester import TheHarvesterRunner
from apps.scanning.tools.whatweb_runner import WhatWebRunner
from apps.scanning.tools.gowitness_runner import GoWitnessRunner
from apps.scanning.tools.testssl_runner import TestsslRunner
from apps.scanning.tools.wafw00f_runner import Wafw00fRunner
from apps.scanning.tools.waybackurls_runner import WaybackUrlsRunner
from apps.scanning.tools.gau_runner import GauRunner
from apps.scanning.tools.dnstwist_runner import DnstwistRunner
from apps.scanning.tools.shodan_runner import ShodanRunner
from apps.scanning.tools.feroxbuster_runner import FeroxbusterRunner


def get_domain_tools(tier):
    """Return ordered list of (ToolRunner, options) for the given tier."""
    # Bronze: core discovery and basic enumeration
    tools = [
        (SubfinderRunner(), {}),
        (AmassRunner(), {}),
        (AssetfinderRunner(), {}),
        (CrtshRunner(), {}),
        (WhoisRunner(), {}),
        (HttpxRunner(), {}),
        (NmapRunner(), {"ports": "--top-ports 1000"}),
        (NucleiRunner(), {"severity": "critical,high,medium"}),
    ]

    if tier in ("silver", "gold"):
        # Insert additional discovery/enumeration tools
        tools.insert(5, (TheHarvesterRunner(), {}))
        tools.append((WhatWebRunner(), {}))
        tools.append((GoWitnessRunner(), {}))
        tools.append((TestsslRunner(), {}))
        tools.append((Wafw00fRunner(), {}))
        tools.append((WaybackUrlsRunner(), {}))
        tools.append((GauRunner(), {}))
        tools.append((DnstwistRunner(), {}))
        tools.append((ShodanRunner(), {}))
        # Upgrade nmap to full port scan
        for i, (tool, opts) in enumerate(tools):
            if tool.name == "nmap":
                tools[i] = (NmapRunner(), {"ports": "1-65535"})

    if tier == "gold":
        tools.append((FeroxbusterRunner(), {}))
        # Upgrade nuclei to include low severity
        for i, (tool, opts) in enumerate(tools):
            if tool.name == "nuclei":
                tools[i] = (NucleiRunner(), {"severity": "critical,high,medium,low"})

    return tools
