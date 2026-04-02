"""
Celery tasks for scanning — these execute on the scanner container (queue='scanning').
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="scanning")
def run_tool_execution(self, tool_execution_id):
    """Execute a single tool and store results."""
    from apps.scanning.models import ToolExecution, DiscoveredAsset

    te = ToolExecution.objects.get(pk=tool_execution_id)
    te.status = "running"
    te.started_at = timezone.now()
    te.save(update_fields=["status", "started_at"])

    runner_class = _get_tool_map().get(te.tool_name)
    if not runner_class:
        te.status = "failed"
        te.raw_output = f"Unknown tool: {te.tool_name}"
        te.save(update_fields=["status", "raw_output"])
        return

    runner = runner_class()
    result = runner.run(te.target)

    te.status = result.get("status", "failed")
    te.exit_code = result.get("exit_code")
    te.raw_output = result.get("raw_output", "")[:50000]
    te.parsed_results = result.get("parsed", {})
    te.command = result.get("command", "")
    te.completed_at = timezone.now()
    te.save()

    # Create discovered assets from parsed results
    scan = te.scan
    engagement = scan.engagement
    _store_discovered_assets(te, scan, engagement)

    return {"tool_execution_id": te.pk, "status": te.status}


@shared_task(bind=True, queue="scanning")
def run_scan_workflow(self, scan_id):
    """Orchestrate a full scan workflow for an engagement."""
    from apps.scanning.models import Scan, ToolExecution
    from apps.scanning.workflows.domain_workflow import get_domain_tools
    from apps.scanning.workflows.ip_workflow import get_ip_tools
    from apps.scanning.workflows.cidr_workflow import get_cidr_tools
    from apps.scanning.workflows.email_workflow import get_email_tools
    from apps.scanning.workflows.name_workflow import get_name_tools
    from apps.scanning.workflows.url_workflow import get_url_tools
    from apps.scanning.workflows.repo_workflow import get_repo_tools

    scan = Scan.objects.get(pk=scan_id)
    scan.status = "running"
    scan.started_at = timezone.now()
    scan.celery_task_id = self.request.id
    scan.save(update_fields=["status", "started_at", "celery_task_id"])

    engagement = scan.engagement
    tier = engagement.tier
    scope_items = engagement.scope_items.filter(in_scope=True)

    WORKFLOW_MAP = {
        "domain": get_domain_tools,
        "ip": get_ip_tools,
        "cidr": get_cidr_tools,
        "email": get_email_tools,
        "name": get_name_tools,
        "url": get_url_tools,
        "repo": get_repo_tools,
    }

    # Collect all tool executions
    total_executions = []
    for scope_item in scope_items:
        workflow_fn = WORKFLOW_MAP.get(scope_item.item_type)
        if not workflow_fn:
            continue
        tools = workflow_fn(tier)
        for tool_runner, options in tools:
            te = ToolExecution.objects.create(
                scan=scan,
                tool_name=tool_runner.name,
                target=scope_item.value,
            )
            total_executions.append((te, tool_runner, options))

    # Execute sequentially within the workflow
    completed = 0
    for te, tool_runner, options in total_executions:
        try:
            te.status = "running"
            te.started_at = timezone.now()
            te.save(update_fields=["status", "started_at"])

            result = tool_runner.run(te.target, options)

            te.status = result.get("status", "failed")
            te.exit_code = result.get("exit_code")
            te.raw_output = result.get("raw_output", "")[:50000]
            te.parsed_results = result.get("parsed", {})
            te.command = result.get("command", "")
            te.completed_at = timezone.now()
            te.save()

            # Store discovered assets
            _store_discovered_assets(te, scan, engagement)

            # Auto-create findings from tool-specific results
            _create_findings_from_parsed(te, scan, engagement)

        except Exception as e:
            te.status = "failed"
            te.raw_output = str(e)
            te.completed_at = timezone.now()
            te.save()
            logger.exception("Tool %s failed on %s", te.tool_name, te.target)

        completed += 1
        scan.progress = int((completed / len(total_executions)) * 100)
        scan.save(update_fields=["progress"])

        # Send WebSocket progress update
        _send_progress(scan)

    scan.status = "completed"
    scan.completed_at = timezone.now()
    scan.progress = 100
    scan.save(update_fields=["status", "completed_at", "progress"])
    _send_progress(scan)

    return {"scan_id": scan.pk, "status": "completed"}


def _get_tool_map():
    """Return a mapping of tool names to runner classes."""
    from apps.scanning.tools.subfinder import SubfinderRunner
    from apps.scanning.tools.amass import AmassRunner
    from apps.scanning.tools.httpx_runner import HttpxRunner
    from apps.scanning.tools.nmap_runner import NmapRunner
    from apps.scanning.tools.nuclei_runner import NucleiRunner
    from apps.scanning.tools.theharvester import TheHarvesterRunner
    from apps.scanning.tools.masscan_runner import MasscanRunner
    from apps.scanning.tools.dnsx_runner import DnsxRunner
    from apps.scanning.tools.testssl_runner import TestsslRunner
    from apps.scanning.tools.wafw00f_runner import Wafw00fRunner
    from apps.scanning.tools.whatweb_runner import WhatWebRunner
    from apps.scanning.tools.waybackurls_runner import WaybackUrlsRunner
    from apps.scanning.tools.gau_runner import GauRunner
    from apps.scanning.tools.assetfinder_runner import AssetfinderRunner
    from apps.scanning.tools.dnstwist_runner import DnstwistRunner
    from apps.scanning.tools.whois_runner import WhoisRunner
    from apps.scanning.tools.gowitness_runner import GoWitnessRunner
    from apps.scanning.tools.feroxbuster_runner import FeroxbusterRunner
    from apps.scanning.tools.shodan_runner import ShodanRunner
    from apps.scanning.tools.trufflehog_runner import TruffleHogRunner
    from apps.scanning.tools.gitleaks_runner import GitleaksRunner
    from apps.scanning.tools.crtsh_runner import CrtshRunner
    from apps.scanning.tools.hibp_runner import HIBPRunner
    from apps.scanning.tools.github_runner import GitHubRunner
    from apps.scanning.tools.email_security_runner import EmailSecurityRunner

    return {
        "subfinder": SubfinderRunner,
        "amass": AmassRunner,
        "httpx": HttpxRunner,
        "nmap": NmapRunner,
        "nuclei": NucleiRunner,
        "theHarvester": TheHarvesterRunner,
        "masscan": MasscanRunner,
        "dnsx": DnsxRunner,
        "testssl": TestsslRunner,
        "wafw00f": Wafw00fRunner,
        "whatweb": WhatWebRunner,
        "waybackurls": WaybackUrlsRunner,
        "gau": GauRunner,
        "assetfinder": AssetfinderRunner,
        "dnstwist": DnstwistRunner,
        "whois": WhoisRunner,
        "gowitness": GoWitnessRunner,
        "feroxbuster": FeroxbusterRunner,
        "shodan": ShodanRunner,
        "trufflehog": TruffleHogRunner,
        "gitleaks": GitleaksRunner,
        "crtsh": CrtshRunner,
        "hibp": HIBPRunner,
        "github": GitHubRunner,
        "email_security": EmailSecurityRunner,
    }


def _store_discovered_assets(te, scan, engagement):
    """Extract and store discovered assets from tool execution results."""
    from apps.scanning.models import DiscoveredAsset

    parsed = te.parsed_results or {}

    # Subdomains from subfinder, amass, assetfinder, crtsh
    for subdomain in parsed.get("subdomains", []):
        DiscoveredAsset.objects.update_or_create(
            engagement=engagement, asset_type="domain", value=subdomain,
            defaults={"scan": scan, "source_tool": te.tool_name},
        )

    # Hosts from httpx, nmap, shodan
    for host in parsed.get("hosts", []):
        if isinstance(host, dict):
            value = host.get("url") or host.get("host") or host.get("ip", "")
            if value:
                DiscoveredAsset.objects.update_or_create(
                    engagement=engagement,
                    asset_type="url" if value.startswith("http") else "ip",
                    value=value,
                    defaults={"scan": scan, "source_tool": te.tool_name, "metadata": host},
                )

    # URLs from waybackurls, gau, feroxbuster
    for url in parsed.get("urls", [])[:500]:
        if url:
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement, asset_type="url", value=url[:500],
                defaults={"scan": scan, "source_tool": te.tool_name},
            )

    # Paths from feroxbuster
    for path in parsed.get("paths", [])[:200]:
        if isinstance(path, dict) and path.get("url"):
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement, asset_type="url", value=path["url"][:500],
                defaults={
                    "scan": scan, "source_tool": te.tool_name,
                    "metadata": {"status": path.get("status"), "content_length": path.get("content_length")},
                },
            )

    # Technologies from whatweb — enrich existing asset
    if parsed.get("technologies"):
        asset, _ = DiscoveredAsset.objects.update_or_create(
            engagement=engagement, asset_type="url",
            value=te.target if te.target.startswith("http") else f"https://{te.target}",
            defaults={"scan": scan, "source_tool": te.tool_name},
        )
        asset.technology_stack = parsed["technologies"]
        asset.save(update_fields=["technology_stack"])

    # Typosquat domains from dnstwist
    for perm in parsed.get("permutations", []):
        if isinstance(perm, dict) and perm.get("domain") and perm.get("dns_a"):
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement, asset_type="domain", value=perm["domain"],
                defaults={
                    "scan": scan, "source_tool": te.tool_name,
                    "metadata": {"typosquat": True, "fuzzer": perm.get("fuzzer"), "dns_a": perm.get("dns_a")},
                },
            )

    # Certificates from crtsh
    for cert in parsed.get("certificates", []):
        if isinstance(cert, dict):
            cn = cert.get("common_name", "")
            if cn and not cn.startswith("*"):
                DiscoveredAsset.objects.update_or_create(
                    engagement=engagement, asset_type="domain", value=cn,
                    defaults={"scan": scan, "source_tool": te.tool_name},
                )

    # Secrets from trufflehog/gitleaks
    for secret in parsed.get("secrets", []):
        if isinstance(secret, dict):
            value = secret.get("detector", secret.get("rule", "secret"))
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement, asset_type="finding",
                value=f"Secret: {value} in {secret.get('file', 'unknown')}"[:500],
                defaults={"scan": scan, "source_tool": te.tool_name, "metadata": secret},
            )

    # WHOIS data — enrich existing domain asset
    if parsed.get("whois_data"):
        asset, _ = DiscoveredAsset.objects.update_or_create(
            engagement=engagement, asset_type="domain", value=te.target,
            defaults={"scan": scan, "source_tool": te.tool_name},
        )
        asset.whois_data = parsed["whois_data"]
        asset.save(update_fields=["whois_data"])

    # Shodan data — store as metadata
    if parsed.get("shodan_data"):
        for port in parsed.get("ports", []):
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement, asset_type="ip",
                value=f"{parsed.get('ip', te.target)}:{port}",
                defaults={"scan": scan, "source_tool": te.tool_name, "metadata": parsed},
            )

    # Findings from nuclei
    for finding in parsed.get("findings", []):
        if isinstance(finding, dict):
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement,
                asset_type="finding",
                value=finding.get("template-id", finding.get("name", str(finding)))[:500],
                defaults={"scan": scan, "source_tool": te.tool_name, "metadata": finding},
            )

    # Breach data from HIBP
    if parsed.get("breaches"):
        _store_breach_records(te, engagement, parsed["breaches"])


def _store_breach_records(te, engagement, breaches):
    """Create BreachRecord instances from HIBP results."""
    from apps.findings.models import BreachRecord
    from datetime import datetime

    for breach in breaches:
        breach_date = None
        if breach.get("breach_date"):
            try:
                breach_date = datetime.strptime(breach["breach_date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        BreachRecord.objects.update_or_create(
            engagement=engagement,
            email_or_domain=te.target,
            breach_name=breach.get("name", "Unknown"),
            defaults={
                "breach_date": breach_date,
                "pwn_count": breach.get("pwn_count", 0),
                "data_classes": breach.get("data_classes", []),
                "source": "hibp",
                "is_verified": breach.get("is_verified", False),
            },
        )


def _create_findings_from_parsed(te, scan, engagement):
    """Auto-create Finding records from tool-specific parsed results."""
    from apps.findings.models import Finding

    parsed = te.parsed_results or {}
    findings_to_create = []

    # Nuclei findings
    for f in parsed.get("findings", []):
        if isinstance(f, dict):
            severity = f.get("severity", f.get("info", {}).get("severity", "info")).lower()
            if severity not in ("critical", "high", "medium", "low", "info"):
                severity = "info"
            findings_to_create.append({
                "title": f.get("template-id", f.get("name", "Nuclei Finding")),
                "severity": severity,
                "description": f.get("info", {}).get("description", f.get("matched-at", "")),
                "evidence": f.get("matched-at", ""),
                "tool_source": "nuclei",
                "references": f.get("info", {}).get("reference", []),
            })

    # Testssl findings — weak ciphers, expired certs
    if te.tool_name == "testssl":
        for key, items in parsed.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("severity", "").upper() in ("HIGH", "CRITICAL", "MEDIUM"):
                        findings_to_create.append({
                            "title": f"SSL/TLS: {item.get('id', key)}",
                            "severity": item.get("severity", "medium").lower(),
                            "description": item.get("finding", ""),
                            "evidence": f"Target: {te.target}",
                            "tool_source": "testssl",
                        })

    # TruffleHog / Gitleaks — leaked secrets
    for secret in parsed.get("secrets", []):
        if isinstance(secret, dict):
            findings_to_create.append({
                "title": f"Leaked Secret: {secret.get('detector', secret.get('rule', 'Unknown'))}",
                "severity": "high" if secret.get("verified", True) else "medium",
                "description": f"Secret found in {secret.get('file', 'unknown')} (commit: {secret.get('commit', 'unknown')[:12]})",
                "evidence": f"File: {secret.get('file', '')} | Source: {secret.get('source', '')}",
                "tool_source": te.tool_name,
            })

    # Email security findings
    if te.tool_name == "email_security":
        if not parsed.get("spf", {}).get("exists"):
            findings_to_create.append({
                "title": f"Missing SPF Record: {parsed.get('domain', te.target)}",
                "severity": "medium",
                "description": "No SPF record found. The domain may be susceptible to email spoofing.",
                "tool_source": "email_security",
            })
        if not parsed.get("dmarc", {}).get("exists"):
            findings_to_create.append({
                "title": f"Missing DMARC Record: {parsed.get('domain', te.target)}",
                "severity": "medium",
                "description": "No DMARC record found. Email spoofing protection is not configured.",
                "tool_source": "email_security",
            })
        elif parsed.get("dmarc", {}).get("policy") == "none":
            findings_to_create.append({
                "title": f"Weak DMARC Policy (p=none): {parsed.get('domain', te.target)}",
                "severity": "low",
                "description": "DMARC policy is set to 'none' which only monitors but does not reject spoofed emails.",
                "tool_source": "email_security",
            })
        if parsed.get("spoofable"):
            findings_to_create.append({
                "title": f"Domain Spoofable: {parsed.get('domain', te.target)}",
                "severity": "high",
                "description": "The domain can be spoofed in email. SPF and/or DMARC controls are insufficient.",
                "tool_source": "email_security",
            })

    # Dedup and create findings
    for f_data in findings_to_create:
        title = f_data["title"][:500]
        existing = Finding.objects.filter(
            engagement=engagement,
            title=title,
            tool_source=f_data.get("tool_source", ""),
        ).exists()
        if not existing:
            Finding.objects.create(
                engagement=engagement,
                scan=scan,
                title=title,
                severity=f_data.get("severity", "info"),
                description=f_data.get("description", ""),
                evidence=f_data.get("evidence", ""),
                tool_source=f_data.get("tool_source", ""),
                recommendation=f_data.get("recommendation", ""),
                references=f_data.get("references", []),
            )


def _send_progress(scan):
    """Send scan progress via WebSocket."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"scan_{scan.pk}",
            {
                "type": "scan.progress",
                "progress": scan.progress,
                "status": scan.status,
                "scan_id": scan.pk,
            },
        )
    except Exception:
        pass  # WebSocket updates are best-effort
