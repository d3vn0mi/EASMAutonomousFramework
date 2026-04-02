"""OpenAI correlation engine."""
import json
import logging
from django.conf import settings
from .base import CorrelationEngine, CorrelationOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert cybersecurity analyst performing External Attack Surface Management (EASM) correlation analysis. You are given discovered assets and vulnerability findings from an EASM assessment.

Your task is to:
1. Identify attack chains — sequences of findings/assets that could be chained together for exploitation
2. Identify patterns — recurring issues across the attack surface
3. Prioritize risks — rank findings by real-world exploitability and business impact
4. Write an executive summary — 2-3 paragraphs suitable for non-technical leadership

Respond in JSON format with keys: attack_chains, patterns, risk_priorities, executive_summary, remediation_plan"""


class OpenAICorrelationEngine(CorrelationEngine):
    def correlate(self, findings, assets, scan_data):
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        context = self.prepare_context(findings, assets, scan_data)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following EASM data:\n\n{context}"},
            ],
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            data = {}

        return CorrelationOutput(
            analysis=response_text,
            attack_chains=data.get("attack_chains", []),
            patterns=data.get("patterns", []),
            risk_priorities=data.get("risk_priorities", []),
            executive_summary=data.get("executive_summary", ""),
            remediation_plan=data.get("remediation_plan", []),
        )
