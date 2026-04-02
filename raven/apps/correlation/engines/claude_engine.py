"""Claude (Anthropic) correlation engine with multi-pass support."""
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
5. Create a remediation plan — prioritized actions with timelines

Respond in JSON format with keys: attack_chains, patterns, risk_priorities, executive_summary, remediation_plan"""


class ClaudeCorrelationEngine(CorrelationEngine):
    def correlate(self, findings, assets, scan_data):
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        context = self.prepare_context(findings, assets, scan_data)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Analyze the following EASM data and provide correlation analysis:\n\n{context}"},
            ],
        )

        response_text = message.content[0].text
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

    def correlate_multi_pass(self, findings, assets, scan_data, enrichment_data=None):
        """Multi-pass correlation: separate LLM calls for deeper analysis."""
        import anthropic
        from apps.correlation.prompts.attack_chains import ATTACK_CHAINS_SYSTEM_PROMPT
        from apps.correlation.prompts.risk_priorities import RISK_PRIORITIES_SYSTEM_PROMPT
        from apps.correlation.prompts.remediation import REMEDIATION_SYSTEM_PROMPT
        from apps.correlation.prompts.executive_summary import EXECUTIVE_SUMMARY_SYSTEM_PROMPT

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        context = self.prepare_context(findings, assets, scan_data, enrichment_data)

        def _call_llm(system_prompt, user_content, max_tokens=4096):
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            text = message.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}

        # Pass 1: Attack chains
        attack_data = _call_llm(
            ATTACK_CHAINS_SYSTEM_PROMPT,
            f"Construct attack chains from this EASM data:\n\n{context}",
        )
        attack_chains = attack_data.get("attack_chains", [])

        # Pass 2: Risk priorities
        risk_data = _call_llm(
            RISK_PRIORITIES_SYSTEM_PROMPT,
            f"Prioritize risks from this EASM data:\n\n{context}",
        )
        risk_priorities = risk_data.get("risk_priorities", [])

        # Pass 3: Remediation plan
        remediation_context = f"{context}\n\n## Attack Chains Identified\n{json.dumps(attack_chains[:10], indent=2)}\n\n## Risk Priorities\n{json.dumps(risk_priorities[:10], indent=2)}"
        remediation_data = _call_llm(
            REMEDIATION_SYSTEM_PROMPT,
            f"Create a remediation plan based on this data:\n\n{remediation_context}",
        )
        remediation_plan = remediation_data.get("remediation_plan", [])

        # Pass 4: Executive summary
        exec_context = f"## Assessment Statistics\n{json.dumps(scan_data, indent=2)}\n\n## Attack Chains\n{json.dumps(attack_chains[:5], indent=2)}\n\n## Top Risks\n{json.dumps(risk_priorities[:5], indent=2)}"
        exec_data = _call_llm(
            EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
            f"Write an executive summary for this EASM assessment:\n\n{exec_context}",
        )
        executive_summary = exec_data.get("executive_summary", "")
        business_impact = "\n".join(
            f"- {r['risk']}: {r['impact']}" for r in exec_data.get("top_risks", [])
        )

        # Identify patterns from attack chains and findings
        patterns = []
        seen = set()
        for chain in attack_chains:
            for step in chain.get("steps", []):
                key = step[:50]
                if key not in seen:
                    seen.add(key)
                    patterns.append({"description": step})

        return CorrelationOutput(
            analysis=json.dumps({
                "attack_chains": attack_chains,
                "risk_priorities": risk_priorities,
                "remediation_plan": remediation_plan,
                "executive_summary": executive_summary,
            }, indent=2),
            attack_chains=attack_chains,
            patterns=patterns[:20],
            risk_priorities=risk_priorities,
            executive_summary=executive_summary,
            remediation_plan=remediation_plan,
            business_impact_analysis=business_impact,
        )
