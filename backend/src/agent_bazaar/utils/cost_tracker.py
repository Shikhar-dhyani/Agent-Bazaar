import logging

logger = logging.getLogger("agent_bazaar.cost")

# USD per million tokens  (input, output)
_PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-sonnet-4-6":         (3.00, 15.00),
}

_DEFAULT_PRICE = (3.00, 15.00)


def log_usage(model: str, usage, caller: str) -> float:
    """Log token counts and estimated USD cost for one API call. Returns cost."""
    in_tok = getattr(usage, "input_tokens", 0) or 0
    out_tok = getattr(usage, "output_tokens", 0) or 0
    in_price, out_price = _PRICING.get(model, _DEFAULT_PRICE)
    cost = (in_tok * in_price + out_tok * out_price) / 1_000_000
    logger.info(
        "[COST] %-35s | model=%-30s | in=%5d  out=%5d | $%.6f",
        caller, model, in_tok, out_tok, cost,
    )
    return cost
