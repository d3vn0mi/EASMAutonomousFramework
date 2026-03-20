"""
Abstract base for AI correlation engines.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CorrelationOutput:
    analysis: str
    attack_chains: list
    patterns: list
    risk_priorities: list
    executive_summary: str
    confidence_score: float | None = None


class CorrelationEngine(ABC):
    """Base class for LLM-based correlation engines."""

    @abstractmethod
    def correlate(self, findings: list[dict], assets: list[dict], scan_data: dict) -> CorrelationOutput:
        """Send data to LLM and return structured analysis."""
        ...

    def prepare_context(self, findings, assets, scan_data):
        """Format engagement data into an LLM prompt context."""
        context = "## Discovered Assets\n"
        for asset in assets[:200]:
            context += f"- [{asset.get('type', 'unknown')}] {asset.get('value', '')}"
            if asset.get("metadata"):
                context += f" (metadata: {str(asset['metadata'])[:200]})"
            context += "\n"

        context += "\n## Findings\n"
        for finding in findings[:100]:
            context += f"- [{finding.get('severity', 'info').upper()}] {finding.get('title', '')}\n"
            if finding.get("description"):
                context += f"  Description: {finding['description'][:300]}\n"
            if finding.get("affected_assets"):
                context += f"  Affected: {', '.join(finding['affected_assets'][:5])}\n"

        context += f"\n## Scan Summary\n"
        context += f"- Total assets discovered: {scan_data.get('total_assets', 0)}\n"
        context += f"- Total findings: {scan_data.get('total_findings', 0)}\n"
        context += f"- Critical: {scan_data.get('critical_count', 0)}\n"
        context += f"- High: {scan_data.get('high_count', 0)}\n"
        context += f"- Medium: {scan_data.get('medium_count', 0)}\n"

        return context
