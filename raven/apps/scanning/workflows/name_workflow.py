"""
Person Name OSINT Workflow
"""
from apps.scanning.tools.theharvester import TheHarvesterRunner


def get_name_tools(tier):
    """Return tools for name-based OSINT."""
    tools = [
        (TheHarvesterRunner(), {}),
    ]
    return tools
