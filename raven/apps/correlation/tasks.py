"""Celery tasks for AI correlation."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="default")
def run_correlation(self, engagement_id, engine_name=None):
    """Run AI correlation analysis on engagement findings."""
    from django.conf import settings
    from apps.engagements.models import Engagement
    from apps.findings.models import Finding
    from apps.scanning.models import DiscoveredAsset
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

    # Gather data
    findings_data = list(
        Finding.objects.filter(engagement=engagement, is_false_positive=False).values(
            "title", "severity", "description", "evidence", "cve_id", "cvss_score",
        )
    )
    assets_data = list(
        DiscoveredAsset.objects.filter(engagement=engagement).values(
            "asset_type", "value", "source_tool", "metadata",
        )
    )
    scan_data = {
        "total_assets": len(assets_data),
        "total_findings": len(findings_data),
        "critical_count": sum(1 for f in findings_data if f["severity"] == "critical"),
        "high_count": sum(1 for f in findings_data if f["severity"] == "high"),
        "medium_count": sum(1 for f in findings_data if f["severity"] == "medium"),
    }

    engine = engine_class()
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
        confidence_score=result.confidence_score,
    )

    return {"correlation_id": correlation.pk, "engine": engine_name}
