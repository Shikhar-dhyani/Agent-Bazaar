import copy
from typing import Dict, List, Optional
from agent_bazaar.models.agent_profile import AgentProfile, AgentTier
from agent_bazaar.models.subtask import Capability

_INITIAL_PROFILES: List[AgentProfile] = [
    # Web Search
    AgentProfile(
        id="web_search_fast",
        name="WebSearch-Fast",
        tier=AgentTier.FAST,
        capabilities=[Capability.WEB_SEARCH.value],
        reputation={Capability.WEB_SEARCH.value: 0.60},
        base_cost=2.0,
        base_latency=3.0,
        model="claude-haiku-4-5-20251001",
    ),
    AgentProfile(
        id="web_search_thorough",
        name="WebSearch-Thorough",
        tier=AgentTier.THOROUGH,
        capabilities=[Capability.WEB_SEARCH.value],
        reputation={Capability.WEB_SEARCH.value: 0.70},
        base_cost=8.0,
        base_latency=10.0,
        model="claude-sonnet-4-6",
    ),
    # Code Generation
    AgentProfile(
        id="code_gen_fast",
        name="CodeGen-Fast",
        tier=AgentTier.FAST,
        capabilities=[Capability.CODE_GENERATION.value],
        reputation={Capability.CODE_GENERATION.value: 0.65},
        base_cost=2.5,
        base_latency=4.0,
        model="claude-haiku-4-5-20251001",
    ),
    AgentProfile(
        id="code_gen_thorough",
        name="CodeGen-Thorough",
        tier=AgentTier.THOROUGH,
        capabilities=[Capability.CODE_GENERATION.value],
        reputation={Capability.CODE_GENERATION.value: 0.80},
        base_cost=9.0,
        base_latency=12.0,
        model="claude-sonnet-4-6",
    ),
    # Data Analysis
    AgentProfile(
        id="data_analysis_fast",
        name="DataAnalysis-Fast",
        tier=AgentTier.FAST,
        capabilities=[Capability.DATA_ANALYSIS.value],
        reputation={Capability.DATA_ANALYSIS.value: 0.60},
        base_cost=2.0,
        base_latency=3.5,
        model="claude-haiku-4-5-20251001",
    ),
    AgentProfile(
        id="data_analysis_thorough",
        name="DataAnalysis-Thorough",
        tier=AgentTier.THOROUGH,
        capabilities=[Capability.DATA_ANALYSIS.value],
        reputation={Capability.DATA_ANALYSIS.value: 0.75},
        base_cost=8.0,
        base_latency=10.0,
        model="claude-sonnet-4-6",
    ),
    # Fact Checking
    AgentProfile(
        id="fact_check_fast",
        name="FactCheck-Fast",
        tier=AgentTier.FAST,
        capabilities=[Capability.FACT_CHECKING.value],
        reputation={Capability.FACT_CHECKING.value: 0.62},
        base_cost=1.5,
        base_latency=2.5,
        model="claude-haiku-4-5-20251001",
    ),
    AgentProfile(
        id="fact_check_thorough",
        name="FactCheck-Thorough",
        tier=AgentTier.THOROUGH,
        capabilities=[Capability.FACT_CHECKING.value],
        reputation={Capability.FACT_CHECKING.value: 0.78},
        base_cost=7.0,
        base_latency=9.0,
        model="claude-sonnet-4-6",
    ),
    # Text Synthesis
    AgentProfile(
        id="text_synthesis_fast",
        name="TextSynthesis-Fast",
        tier=AgentTier.FAST,
        capabilities=[Capability.TEXT_SYNTHESIS.value],
        reputation={Capability.TEXT_SYNTHESIS.value: 0.65},
        base_cost=1.5,
        base_latency=2.0,
        model="claude-haiku-4-5-20251001",
    ),
    AgentProfile(
        id="text_synthesis_thorough",
        name="TextSynthesis-Thorough",
        tier=AgentTier.THOROUGH,
        capabilities=[Capability.TEXT_SYNTHESIS.value],
        reputation={Capability.TEXT_SYNTHESIS.value: 0.75},
        base_cost=6.0,
        base_latency=8.0,
        model="claude-sonnet-4-6",
    ),
]

_registry: Dict[str, AgentProfile] = {}


def _ensure_loaded() -> None:
    if not _registry:
        for profile in _INITIAL_PROFILES:
            _registry[profile.id] = copy.deepcopy(profile)


def get_registry() -> Dict[str, AgentProfile]:
    _ensure_loaded()
    return _registry


def get_agent(agent_id: str) -> Optional[AgentProfile]:
    _ensure_loaded()
    return _registry.get(agent_id)


def get_agents_for_capability(capability: str) -> List[AgentProfile]:
    _ensure_loaded()
    return [a for a in _registry.values() if capability in a.capabilities]


def update_agent(profile: AgentProfile) -> None:
    _ensure_loaded()
    _registry[profile.id] = profile
