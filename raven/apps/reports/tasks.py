"""Celery tasks for report generation."""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="default")
def generate_report(self, engagement_id, report_type, user_id, report_format="docx"):
    """Generate a report (executive or technical) for an engagement."""
    from apps.accounts.models import User
    from apps.engagements.models import Engagement, EngagementDocument
    from apps.reports.models import Report

    engagement = Engagement.objects.get(pk=engagement_id)
    user = User.objects.get(pk=user_id)

    if report_format == "html":
        from apps.reports.generators.html_generator import generate_html_report
        output_path = generate_html_report(engagement, report_type)
    elif report_format == "pdf":
        from apps.reports.generators.pdf_generator import generate_pdf_report
        output_path = generate_pdf_report(engagement, report_type)
    else:
        from apps.reports.generators.docx_generator import (
            generate_executive_report,
            generate_technical_report,
        )
        generator = {
            "executive": generate_executive_report,
            "technical": generate_technical_report,
        }.get(report_type)
        if not generator:
            return {"error": f"Unknown report type: {report_type}"}
        output_path = generator(engagement)

    report = Report.objects.create(
        engagement=engagement,
        report_type=report_type,
        report_format=report_format,
        status="generated",
        generated_file=output_path,
        template_used=f"RAVEN_Report_{engagement.tier.title()}.{report_format}",
        generated_at=timezone.now(),
    )

    doc_type = f"report_{report_type[:4]}"
    EngagementDocument.objects.create(
        engagement=engagement,
        doc_type=doc_type,
        file=output_path,
        generated_by=user,
    )

    return {"report_id": report.pk, "path": str(output_path)}
