"""
Generate PDF reports by converting HTML reports via WeasyPrint.
"""
import os
import logging
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_pdf_report(engagement, report_type="technical"):
    """
    Generate an HTML report then convert to PDF via WeasyPrint.
    Returns the relative path to the generated PDF file.
    """
    from .html_generator import generate_html_report
    from weasyprint import HTML

    html_rel_path = generate_html_report(engagement, report_type)
    html_abs_path = os.path.join(settings.MEDIA_ROOT, html_rel_path)

    output_dir = os.path.join(settings.MEDIA_ROOT, "reports", str(datetime.now().year))
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{engagement.engagement_id}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(output_dir, filename)

    HTML(filename=html_abs_path).write_pdf(pdf_path)
    logger.info("PDF report generated: %s", pdf_path)

    return os.path.relpath(pdf_path, settings.MEDIA_ROOT)
