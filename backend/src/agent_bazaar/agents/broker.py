import json
from typing import List
import anthropic
from agent_bazaar.models.task import Task
from agent_bazaar.models.subtask import Subtask, Capability
from agent_bazaar.config import settings
from agent_bazaar.utils.cost_tracker import log_usage

_BROKER_SYSTEM = """You are a task decomposition broker for a multi-agent marketplace.
Break the given task into 2–6 atomic subtasks that specialist agents will bid on and execute.

Rules:
- Each subtask must map to exactly one capability: web_search, code_generation, data_analysis, fact_checking, or text_synthesis
- Use dependency_ids to express ordering — a subtask lists IDs of subtasks it depends on
- Independent subtasks should have empty dependency_ids so they can run in parallel conceptually
- Keep descriptions specific and actionable

Return ONLY a JSON array with no markdown wrapper. Each object must have:
  id (string, e.g. "st_0"), description (string), required_capability (string), dependency_ids (array of strings), order (integer)"""

_BROKER_PROMPT = "Decompose this task into atomic subtasks:\n\n{request}"


class BrokerAgent:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def decompose(self, task: Task) -> List[Subtask]:
        response = await self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=_BROKER_SYSTEM,
            messages=[{"role": "user", "content": _BROKER_PROMPT.format(request=task.raw_request)}],
        )
        log_usage("claude-sonnet-4-6", response.usage, "broker/decompose")
        raw = response.content[0].text.strip()
        # Strip accidental markdown fences
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)

        # First pass: build a stable mapping from whatever the LLM used as IDs
        # (integers, "st_0" strings, arbitrary strings) to our canonical "st_N" IDs.
        # This prevents mismatches like id="st_0" vs dependency_ids=["0"].
        llm_to_ours: dict[str, str] = {}
        for i, item in enumerate(data):
            llm_id = str(item.get("id", i))
            llm_to_ours[llm_id] = f"st_{i}"

        subtasks: List[Subtask] = []
        for i, item in enumerate(data):
            our_id = f"st_{i}"
            cap_str = item.get("required_capability", "text_synthesis")
            try:
                capability = Capability(cap_str)
            except ValueError:
                capability = Capability.TEXT_SYNTHESIS

            raw_deps = item.get("dependency_ids", [])
            dep_ids = [llm_to_ours.get(str(d), str(d)) for d in raw_deps]

            subtasks.append(
                Subtask(
                    id=our_id,
                    parent_task_id=task.id,
                    description=str(item.get("description", "")),
                    required_capability=capability,
                    dependency_ids=dep_ids,
                    order=int(item.get("order", i)),
                )
            )
        return subtasks
