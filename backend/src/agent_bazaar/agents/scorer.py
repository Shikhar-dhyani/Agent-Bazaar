import json
from agent_bazaar.models.subtask import Subtask
from agent_bazaar.config import settings
from agent_bazaar.utils.llm_client import complete
from agent_bazaar.utils.cost_tracker import log_usage

_SCORER_SYSTEM = "You are a quality assessment agent. Return only valid JSON."

_SCORER_PROMPT = """Evaluate the quality of this subtask execution:

SUBTASK: {description}
CAPABILITY: {capability}

AGENT OUTPUT:
{output}

Score on a 0.0–1.0 scale:
  0.0 = completely wrong or empty
  0.5 = adequate but incomplete
  1.0 = excellent, comprehensive

Return JSON only: {{"score": <float>, "feedback": "<one sentence>"}}"""


class ScorerAgent:
    async def score(self, subtask: Subtask, output: str) -> tuple[float, str]:
        prompt = _SCORER_PROMPT.format(
            description=subtask.description,
            capability=subtask.required_capability.value,
            output=output[:3000],
        )
        try:
            text, response = await complete(settings.scorer_model, _SCORER_SYSTEM, prompt, max_tokens=256)
            log_usage(settings.scorer_model, response, "scorer/score")
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            score = max(0.0, min(1.0, float(data.get("score", 0.5))))
            feedback = str(data.get("feedback", "Scored"))
            return round(score, 3), feedback
        except Exception:
            return 0.5, "Scoring unavailable"
