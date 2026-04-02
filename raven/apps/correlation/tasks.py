"""Celery tasks for AI correlation."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="default")
def run_correlation(self, engagement_id, engine_name=None):
    """Run AI correlation analysis on engagement findings."""
    from django.conf import settings
    from apps.engagements.models import Engagement
    from apps.findings.models import Finding, BreachRecord
    from apps.scanning.models import DiscoveredAsset, ToolExecution, Scan
    from apps.correlation.models import CorrelationResult
    from apps.correlation.engines.claude_engine import ClaudeCorrelationEngine
    from apps.correlation.engines.openai_engine import OpenAICorrelationEngine
    from apps.correlation.engines.ollama_engine import OllamaCorrelationEngine

    ENGINE_MAP = {
        "claude": ClaudeCorrelationEngine,
        "openai": OpenAICorrelationEngine,
        "ollama": OllamaCorrelationEngine,
    }

    engine_name = engine_name or settings.CORRELATION_ENGINE
    engine_class = ENGINE_MAP.get(engine_name)
    if not engine_class:
        return {"error": f"Unknown engine: {engine_name}"}

    engagement = Engagement.objects.get(pk=engagement_id)

    # Gather findings data
    findings_data = list(
        Finding.objects.filter(engagement=engagement, is_false_positive=False).values(
            "title", "severity", "description", "evidence", "cve_id", "cvss_score",
            "epss_score", "business_impact", "tool_source",
        )
    )
    assets_data = list(
        DiscoveredAsset.objects.filter(engagement=engagement).values(
            "asset_type", "value", "source_tool", "metadata",
            "technology_stack", "ssl_info", "whois_data",
        )
    )
    scan_data = {
        "total_assets": len(assets_data),
        "total_findings": len(findings_data),
        "critical_count": sum(1 for f in findings_data if f["severity"] == "critical"),
        "high_count": sum(1 for f in findings_data if f["severity"] == "high"),
        "medium_count": sum(1 for f in findings_data if f["severity"] == "medium"),
    }

    # Gather enrichment data from tool executions
    enrichment_data = _gather_enrichment(engagement)

    engine = engine_class()

    # Use multi-pass for Gold tier, single-pass otherwise
    if engagement.tier == "gold" and hasattr(engine, "correlate_multi_pass"):
        result = engine.correlate_multi_pass(findings_data, assets_data, scan_data, enrichment_data)
    else:
        result = engine.correlate(findings_data, assets_data, scan_data)

    correlation = CorrelationResult.objects.create(
        engagement=engagement,
        engine_used=engine_name,
        input_summary=scan_data,
        output=result.analysis,
        attack_chains=result.attack_chains,
        patterns=result.patterns,
        risk_priorities=result.risk_priorities,
        executive_summary=result.executive_summary,
        remediation_plan=result.remediation_plan,
        business_impact_analysis=result.business_impact_analysis,
        confidence_score=result.confidence_score,
    )

    return {"correlation_id": correlation.pk, "engine": engine_name}


def _gather_enrichment(engagement):
    """Gather enrichment data from tool executions for richer correlation."""
    from apps.scanning.models import ToolExecution, Scan
    from apps.findings.models import BreachRecord

    scans = Scan.objects.filter(engagement=engagement)
    tool_executions = ToolExecution.objects.filter(
        scan__in=scans, status="completed",
    )

    enrichment = {}

    for te in tool_executions:
        parsed = te.parsed_results or {}

        if te.tool_name == "whois" and parsed.get("whois_data"):
            enrichment.setdefault("whois", []).append(
                str(parsed["whois_data"])[:500]
            )
        elif te.tool_name == "dnsx" and parsed.get("records"):
            for record in parsed["records"][:20]:
                enrichment.setdefault("dns", []).append(str(record)[:200])
        elif te.tool_name == "testssl":
            enrichment.setdefault("ssl", []).append(
                str(parsed)[:500]
            )
        elif te.tool_name == "whatweb" and parsed.get("technologies"):
            for tech in parsed["technologies"][:20]:
                enrichment.setdefault("technologies", []).append(
                    f"{tech.get('name', '')} {tech.get('version', '')}"
                )
        elif te.tool_name == "email_security":
            enrichment.setdefault("email_security", []).append(
                str(parsed)[:500]
            )
        elif te.tool_name == "shodan":
            enrichment.setdefault("shodan", []).append(
                str(parsed)[:500]
            )

    # Breach records
    breach_records = BreachRecord.objects.filter(engagement=engagement)
    if breach_records.exists():
        enrichment["breaches"] = [
            f"{b.breach_name} ({b.email_or_domain}): {', '.join(b.data_classes[:5])}"
            for b in breach_records[:20]
        ]

    return enrichment
