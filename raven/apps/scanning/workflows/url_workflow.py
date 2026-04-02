"""
URL / Web Application Workflow
Tier determines depth:
  - Bronze: httpx, whatweb, nuclei
  - Silver: + feroxbuster, gowitness, testssl, wafw00f
  - Gold: + nuclei all severities
"""
from apps.scanning.tools.httpx_runner import HttpxRunner
from apps.scanning.tools.whatweb_runner import WhatWebRunner
from apps.scanning.tools.nuclei_runner import NucleiRunner
from apps.scanning.tools.feroxbuster_runner import FeroxbusterRunner
from apps.scanning.tools.gowitness_runner import GoWitnessRunner
from apps.scanning.tools.testssl_runner import TestsslRunner
from apps.scanning.tools.wafw00f_runner import Wafw00fRunner


def get_url_tools(tier):
    """Return ordered list of (ToolRunner, options) for URL targets."""
    tools = [
        (HttpxRunner(), {}),
        (WhatWebRunner(), {}),
        (NucleiRunner(), {"severity": "critical,high,medium"}),
    ]

    if tier in ("silver", "gold"):
        tools.append((FeroxbusterRunner(), {}))
        tools.append((GoWitnessRunner(), {}))
        tools.append((TestsslRunner(), {}))
        tools.append((Wafw00fRunner(), {}))

    if tier == "gold":
        for i, (tool, opts) in enumerate(tools):
            if tool.name == "nuclei":
                tools[i] = (NucleiRunner(), {"severity": "critical,high,medium,low"})

    return tools
