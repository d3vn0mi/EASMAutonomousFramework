"""Ollama (local LLM) correlation engine for air-gapped deployments."""
import json
import logging
import requests
from django.conf import settings
from .base import CorrelationEngine, CorrelationOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert cybersecurity analyst performing EASM correlation analysis.
Analyze the provided assets and findings. Respond in JSON with keys: attack_chains, patterns, risk_priorities, executive_summary, remediation_plan"""


class OllamaCorrelationEngine(CorrelationEngine):
    def correlate(self, findings, assets, scan_data):
        context = self.prepare_context(findings, assets, scan_data)
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")

        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": "llama3.1",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze:\n\n{context}"},
                ],
                "stream": False,
                "format": "json",
            },
            timeout=300,
        )
        response.raise_for_status()

        response_text = response.json().get("message", {}).get("content", "")
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
