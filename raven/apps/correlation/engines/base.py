"""
Abstract base for AI correlation engines.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CorrelationOutput:
    analysis: str
    attack_chains: list
    patterns: list
    risk_priorities: list
    executive_summary: str
    remediation_plan: list = field(default_factory=list)
    business_impact_analysis: str = ""
    confidence_score: float | None = None


class CorrelationEngine(ABC):
    """Base class for LLM-based correlation engines."""

    @abstractmethod
    def correlate(self, findings: list[dict], assets: list[dict], scan_data: dict) -> CorrelationOutput:
        """Send data to LLM and return structured analysis."""
        ...

    def correlate_multi_pass(self, findings, assets, scan_data, enrichment_data=None):
        """Multi-pass correlation for Gold tier: separate passes for deeper analysis."""
        return self.correlate(findings, assets, scan_data)

    def prepare_context(self, findings, assets, scan_data, enrichment_data=None):
        """Format engagement data into an LLM prompt context."""
        context = "## Discovered Assets\n"
        for asset in assets[:500]:
            context += f"- [{asset.get('type', asset.get('asset_type', 'unknown'))}] {asset.get('value', '')}"
            if asset.get("metadata"):
                meta_str = str(asset['metadata'])[:300]
                context += f" (metadata: {meta_str})"
            if asset.get("technology_stack"):
                context += f" [tech: {', '.join(str(t) for t in asset['technology_stack'][:5])}]"
            context += "\n"

        context += "\n## Findings\n"
        for finding in findings[:250]:
            context += f"- [{finding.get('severity', 'info').upper()}] {finding.get('title', '')}\n"
            if finding.get("description"):
                context += f"  Description: {finding['description'][:400]}\n"
            if finding.get("affected_assets"):
                affected = finding['affected_assets']
                if isinstance(affected, list):
                    context += f"  Affected: {', '.join(str(a) for a in affected[:5])}\n"
            if finding.get("cvss_score"):
                context += f"  CVSS: {finding['cvss_score']}\n"
            if finding.get("epss_score"):
                context += f"  EPSS: {finding['epss_score']}\n"
            if finding.get("cve_id"):
                context += f"  CVE: {finding['cve_id']}\n"

        context += f"\n## Scan Summary\n"
        context += f"- Total assets discovered: {scan_data.get('total_assets', 0)}\n"
        context += f"- Total findings: {scan_data.get('total_findings', 0)}\n"
        context += f"- Critical: {scan_data.get('critical_count', 0)}\n"
        context += f"- High: {scan_data.get('high_count', 0)}\n"
        context += f"- Medium: {scan_data.get('medium_count', 0)}\n"

        # Enrichment data
        if enrichment_data:
            if enrichment_data.get("whois"):
                context += "\n## WHOIS Data\n"
                for wd in enrichment_data["whois"][:5]:
                    context += f"- {wd}\n"

            if enrichment_data.get("dns"):
                context += "\n## DNS Records\n"
                for record in enrichment_data["dns"][:20]:
                    context += f"- {record}\n"

            if enrichment_data.get("ssl"):
                context += "\n## SSL/TLS Information\n"
                for ssl in enrichment_data["ssl"][:10]:
                    context += f"- {ssl}\n"

            if enrichment_data.get("technologies"):
                context += "\n## Technology Stack\n"
                for tech in enrichment_data["technologies"][:30]:
                    context += f"- {tech}\n"

            if enrichment_data.get("email_security"):
                context += "\n## Email Security\n"
                for es in enrichment_data["email_security"][:5]:
                    context += f"- {es}\n"

            if enrichment_data.get("breaches"):
                context += "\n## Breach Records\n"
                for breach in enrichment_data["breaches"][:20]:
                    context += f"- {breach}\n"

            if enrichment_data.get("shodan"):
                context += "\n## Shodan Intelligence\n"
                for item in enrichment_data["shodan"][:20]:
                    context += f"- {item}\n"

        return context
