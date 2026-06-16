import json
import anthropic
from agent_bazaar.models.bid import Bid
from agent_bazaar.models.subtask import Subtask
from agent_bazaar.models.agent_profile import AgentProfile
from agent_bazaar.config import settings

_BID_SYSTEM = "You are a specialist agent assessing a bid. Return only valid JSON, no markdown."

_BID_PROMPT = """You are {name}, a specialist in {capability} (tier: {tier}).

Assess this subtask and submit your bid:
SUBTASK: {description}

CONTEXT FROM COMPLETED SUBTASKS:
{context}

Your base cost: {base_cost}, base latency: {base_latency}s

Evaluate your confidence and estimate your cost/latency multipliers.
Return JSON only:
{{
  "confidence": <float 0.0–1.0>,
  "cost_multiplier": <float 0.5–3.0>,
  "latency_multiplier": <float 0.5–3.0>,
  "rationale": "<one sentence>"
}}"""

_EXECUTE_SYSTEM = "You are a specialist agent. Execute the given subtask thoroughly and return a complete, high-quality result."

_EXECUTE_PROMPT = """You are {name}, a specialist in {capability}.

You won the auction for this subtask. Execute it now.

SUBTASK: {description}

CONTEXT FROM PREVIOUSLY COMPLETED SUBTASKS:
{context}

Provide a complete, well-structured response."""


class BaseSpecialist:
    def __init__(self, profile: AgentProfile) -> None:
        self.profile = profile
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def bid(self, subtask: Subtask, context: str = "") -> Bid:
        capability = subtask.required_capability.value
        if capability not in self.profile.capabilities:
            return Bid(
                subtask_id=subtask.id,
                agent_id=self.profile.id,
                confidence_score=0.01,
                estimated_cost=self.profile.base_cost * 3,
                estimated_latency=self.profile.base_latency * 3,
                rationale="Outside my capability domain",
            )

        prompt = _BID_PROMPT.format(
            name=self.profile.name,
            capability=capability,
            tier=self.profile.tier.value,
            description=subtask.description,
            context=context or "None",
            base_cost=self.profile.base_cost,
            base_latency=self.profile.base_latency,
        )

        try:
            response = await self._client.messages.create(
                model=self.profile.model,
                max_tokens=512,
                system=_BID_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)

            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            cost_mult = max(0.5, min(3.0, float(data.get("cost_multiplier", 1.0))))
            latency_mult = max(0.5, min(3.0, float(data.get("latency_multiplier", 1.0))))

            return Bid(
                subtask_id=subtask.id,
                agent_id=self.profile.id,
                confidence_score=round(confidence, 3),
                estimated_cost=round(self.profile.base_cost * cost_mult, 2),
                estimated_latency=round(self.profile.base_latency * latency_mult, 2),
                rationale=str(data.get("rationale", "Self-assessed bid")),
            )
        except Exception as exc:
            return Bid(
                subtask_id=subtask.id,
                agent_id=self.profile.id,
                confidence_score=0.5,
                estimated_cost=self.profile.base_cost,
                estimated_latency=self.profile.base_latency,
                rationale=f"Default bid (error: {str(exc)[:60]})",
            )

    async def execute(self, subtask: Subtask, context: str = "") -> str:
        prompt = _EXECUTE_PROMPT.format(
            name=self.profile.name,
            capability=subtask.required_capability.value,
            description=subtask.description,
            context=context or "None",
        )
        response = await self._client.messages.create(
            model=self.profile.model,
            max_tokens=2048,
            system=_EXECUTE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
