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

    TOOL_MAP = {
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
    }

    te = ToolExecution.objects.get(pk=tool_execution_id)
    te.status = "running"
    te.started_at = timezone.now()
    te.save(update_fields=["status", "started_at"])

    runner_class = TOOL_MAP.get(te.tool_name)
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
    parsed = result.get("parsed", {})
    scan = te.scan
    engagement = scan.engagement

    subdomains = parsed.get("subdomains", [])
    for subdomain in subdomains:
        DiscoveredAsset.objects.update_or_create(
            engagement=engagement,
            asset_type="domain",
            value=subdomain,
            defaults={"scan": scan, "source_tool": te.tool_name},
        )

    hosts = parsed.get("hosts", [])
    for host in hosts:
        if isinstance(host, dict):
            value = host.get("url") or host.get("host") or host.get("ip", "")
            if value:
                DiscoveredAsset.objects.update_or_create(
                    engagement=engagement,
                    asset_type="url" if value.startswith("http") else "ip",
                    value=value,
                    defaults={"scan": scan, "source_tool": te.tool_name, "metadata": host},
                )

    return {"tool_execution_id": te.pk, "status": te.status}


@shared_task(bind=True, queue="scanning")
def run_scan_workflow(self, scan_id):
    """Orchestrate a full scan workflow for an engagement."""
    from apps.scanning.models import Scan, ToolExecution
    from apps.scanning.workflows.domain_workflow import get_domain_tools
    from apps.scanning.workflows.ip_workflow import get_ip_tools
    from apps.scanning.workflows.email_workflow import get_email_tools
    from apps.scanning.workflows.name_workflow import get_name_tools

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
        "cidr": get_ip_tools,
        "email": get_email_tools,
        "name": get_name_tools,
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


def _store_discovered_assets(te, scan, engagement):
    """Extract and store discovered assets from tool execution results."""
    from apps.scanning.models import DiscoveredAsset

    parsed = te.parsed_results or {}

    for subdomain in parsed.get("subdomains", []):
        DiscoveredAsset.objects.update_or_create(
            engagement=engagement, asset_type="domain", value=subdomain,
            defaults={"scan": scan, "source_tool": te.tool_name},
        )

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

    for finding in parsed.get("findings", []):
        if isinstance(finding, dict):
            DiscoveredAsset.objects.update_or_create(
                engagement=engagement,
                asset_type="finding",
                value=finding.get("template-id", finding.get("name", str(finding)))[:500],
                defaults={"scan": scan, "source_tool": te.tool_name, "metadata": finding},
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
