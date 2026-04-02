"""
Email OSINT Workflow
Tier determines depth:
  - Bronze: theHarvester
  - Silver: + email security checks (SPF/DKIM/DMARC), HIBP breach check
  - Gold: same as Silver
"""
from apps.scanning.tools.theharvester import TheHarvesterRunner
from apps.scanning.tools.email_security_runner import EmailSecurityRunner
from apps.scanning.tools.hibp_runner import HIBPRunner


def get_email_tools(tier):
    """Return tools for email-based reconnaissance."""
    tools = [
        (TheHarvesterRunner(), {}),
    ]

    if tier in ("silver", "gold"):
        tools.append((EmailSecurityRunner(), {}))
        tools.append((HIBPRunner(), {}))

    return tools
