import os
from celery import shared_task
from django.conf import settings


@shared_task(bind=True, queue="default")
def generate_engagement_document(self, engagement_id, doc_type, user_id):
    """Generate a document (SoW, RoE, etc.) from templates."""
    from apps.accounts.models import User
    from apps.engagements.models import Engagement, EngagementDocument
    from apps.reports.generators.docx_generator import generate_document_from_template

    engagement = Engagement.objects.get(pk=engagement_id)
    user = User.objects.get(pk=user_id)

    # Map doc_type to template filename
    template_map = {
        "sow": "RAVEN_SoW_Template",
        "roe": "RAVEN_RoE_Template",
    }
    base_name = template_map.get(doc_type)
    if not base_name:
        return {"error": f"Unknown document type: {doc_type}"}

    lang_suffix = "_GR" if engagement.language == "el" else ""
    template_path = os.path.join(
        settings.RAVEN_TEMPLATES_DIR,
        f"{base_name}{lang_suffix}.docx",
    )

    output_path = generate_document_from_template(
        template_path=template_path,
        engagement=engagement,
        doc_type=doc_type,
    )

    doc = EngagementDocument.objects.create(
        engagement=engagement,
        doc_type=doc_type,
        file=output_path,
        generated_by=user,
    )
    return {"document_id": doc.pk, "path": str(output_path)}
