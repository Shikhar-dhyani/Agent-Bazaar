import logging
import litellm

logger = logging.getLogger("agent_bazaar.cost")

# Fallback pricing (USD per million tokens) for models LiteLLM doesn't yet know
_FALLBACK: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001":        (0.80,  4.00),
    "claude-sonnet-4-6":                (3.00, 15.00),
    "gemini/gemini-2.5-flash":          (0.15,  0.60),
    "gemini/gemini-2.5-flash-lite":     (0.075, 0.30),
    "gemini/gemini-2.5-pro":            (1.25,  10.00),
    "gemini/gemini-2.0-flash":          (0.10,  0.40),
    "gemini/gemini-2.0-flash-lite":     (0.075, 0.30),
    "gemini/gemini-1.5-flash":          (0.075, 0.30),
    "gemini/gemini-1.5-pro":            (1.25,  5.00),
}


def log_usage(model: str, response, caller: str) -> float:
    """Log token counts and USD cost for one API call. Returns cost."""
    usage = getattr(response, "usage", None) or {}
    in_tok  = getattr(usage, "prompt_tokens",     0) or 0
    out_tok = getattr(usage, "completion_tokens",  0) or 0

    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        in_p, out_p = _FALLBACK.get(model, (3.00, 15.00))
        cost = (in_tok * in_p + out_tok * out_p) / 1_000_000

    logger.info(
        "[COST] %-40s | model=%-35s | in=%5d  out=%5d | $%.6f",
        caller, model, in_tok, out_tok, cost,
    )
    return cost
