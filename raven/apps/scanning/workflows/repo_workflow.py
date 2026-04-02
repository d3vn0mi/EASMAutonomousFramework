"""
Code Repository Workflow
Scans Git repositories for leaked secrets and credentials.
  - Bronze: trufflehog
  - Silver: + gitleaks
  - Gold: same as Silver
"""
from apps.scanning.tools.trufflehog_runner import TruffleHogRunner
from apps.scanning.tools.gitleaks_runner import GitleaksRunner


def get_repo_tools(tier):
    """Return tools for repository secret scanning."""
    tools = [
        (TruffleHogRunner(), {}),
    ]

    if tier in ("silver", "gold"):
        tools.append((GitleaksRunner(), {}))

    return tools
