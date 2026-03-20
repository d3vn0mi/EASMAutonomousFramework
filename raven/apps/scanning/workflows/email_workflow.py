"""
Email OSINT Workflow
"""
from apps.scanning.tools.theharvester import TheHarvesterRunner


def get_email_tools(tier):
    """Return tools for email-based reconnaissance."""
    tools = [
        (TheHarvesterRunner(), {}),
    ]
    return tools
