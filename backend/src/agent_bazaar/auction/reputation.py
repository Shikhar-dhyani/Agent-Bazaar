from agent_bazaar.models.agent_profile import AgentProfile

EMA_ALPHA = 0.20
DEFAULT_REPUTATION = 0.50


def update_reputation(
    profile: AgentProfile,
    capability: str,
    quality_score: float,
    alpha: float = EMA_ALPHA,
) -> tuple[AgentProfile, float, float]:
    old_rep = profile.reputation.get(capability, DEFAULT_REPUTATION)
    new_rep = alpha * quality_score + (1 - alpha) * old_rep
    profile.reputation[capability] = round(new_rep, 4)

    if quality_score >= 0.6:
        profile.total_tasks_completed += 1
    else:
        profile.total_tasks_failed += 1

    return profile, old_rep, round(new_rep, 4)
