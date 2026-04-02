"""
Generate rich HTML reports from engagement data.
Produces a self-contained HTML document with inline CSS matching the
15-section RAVEN EASM report structure.
"""
import os
import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generate_html_report(engagement, report_type="technical"):
    """
    Render a data-rich HTML report using Django templates.
    Returns the relative path to the generated file.
    """
    context = _gather_report_data(engagement, report_type)

    template_name = "reports/html_report.html"
    html_content = render_to_string(template_name, context)

    output_dir = os.path.join(settings.MEDIA_ROOT, "reports", str(datetime.now().year))
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{engagement.engagement_id}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return os.path.relpath(output_path, settings.MEDIA_ROOT)


def _gather_report_data(engagement, report_type):
    """Gather all engagement data for report rendering."""
    from apps.findings.models import Finding, BreachRecord
    from apps.scanning.models import DiscoveredAsset, ToolExecution, Scan
    from apps.correlation.models import CorrelationResult

    # Findings grouped by severity
    findings = Finding.objects.filter(
        engagement=engagement, is_false_positive=False,
    ).select_related("scan")
    findings_by_severity = {}
    for sev in ["critical", "high", "medium", "low", "info"]:
        findings_by_severity[sev] = findings.filter(severity=sev)

    # Assets grouped by type
    assets = DiscoveredAsset.objects.filter(engagement=engagement)
    assets_by_type = {}
    for asset in assets:
        assets_by_type.setdefault(asset.asset_type, []).append(asset)

    # Tool executions
    scans = Scan.objects.filter(engagement=engagement)
    tool_executions = ToolExecution.objects.filter(
        scan__in=scans, status="completed",
    ).order_by("created_at")

    # Extract specific tool data
    whois_data = _extract_tool_data(tool_executions, "whois", "whois_data")
    dns_data = _extract_tool_data(tool_executions, "dnsx", "records")
    ssl_data = _extract_tool_data(tool_executions, "testssl")
    tech_data = _extract_tool_data(tool_executions, "whatweb", "technologies")
    email_security = _extract_tool_data(tool_executions, "email_security")
    shodan_data = _extract_tool_data(tool_executions, "shodan")
    wayback_urls = _extract_tool_data(tool_executions, "waybackurls", "urls")
    gau_urls = _extract_tool_data(tool_executions, "gau", "urls")
    dnstwist_data = _extract_tool_data(tool_executions, "dnstwist", "permutations")
    screenshots = _extract_tool_data(tool_executions, "gowitness", "screenshots")
    secret_findings = _extract_tool_data(tool_executions, "trufflehog", "secrets")
    gitleaks_findings = _extract_tool_data(tool_executions, "gitleaks", "secrets")

    # Breach records
    breach_records = BreachRecord.objects.filter(engagement=engagement)

    # Correlation results
    correlation = CorrelationResult.objects.filter(
        engagement=engagement,
    ).order_by("-created_at").first()

    # Summary stats
    summary = {
        "total_findings": findings.count(),
        "critical_count": findings_by_severity["critical"].count(),
        "high_count": findings_by_severity["high"].count(),
        "medium_count": findings_by_severity["medium"].count(),
        "low_count": findings_by_severity["low"].count(),
        "info_count": findings_by_severity["info"].count(),
        "total_assets": assets.count(),
        "total_subdomains": len(assets_by_type.get("domain", [])),
        "total_breaches": breach_records.count(),
    }

    # Scope items
    scope_items = engagement.scope_items.filter(in_scope=True)

    # Combine historical URLs
    historical_urls = list(set(
        (wayback_urls or []) + (gau_urls or [])
    ))[:200]

    return {
        "engagement": engagement,
        "client": engagement.client,
        "report_type": report_type,
        "generated_date": datetime.now().strftime("%B %d, %Y"),
        "scope_items": scope_items,
        "summary": summary,
        "findings": findings,
        "findings_by_severity": findings_by_severity,
        "assets": assets,
        "assets_by_type": assets_by_type,
        "tool_executions": tool_executions,
        "whois_data": whois_data,
        "dns_data": dns_data,
        "ssl_data": ssl_data,
        "tech_data": tech_data,
        "email_security": email_security,
        "shodan_data": shodan_data,
        "historical_urls": historical_urls,
        "dnstwist_data": dnstwist_data,
        "screenshots": screenshots,
        "secret_findings": (secret_findings or []) + (gitleaks_findings or []),
        "breach_records": breach_records,
        "correlation": correlation,
    }


def _extract_tool_data(tool_executions, tool_name, key=None):
    """Extract parsed data from a specific tool's executions."""
    results = []
    for te in tool_executions:
        if te.tool_name == tool_name and te.parsed_results:
            if key:
                data = te.parsed_results.get(key, [])
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict):
                    results.append(data)
            else:
                results.append(te.parsed_results)
    return results if results else None
