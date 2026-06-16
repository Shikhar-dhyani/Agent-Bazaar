"""
Thin wrapper around LiteLLM so every API call goes through one place.
To switch provider: change the model name string passed to complete().

  Anthropic : "claude-sonnet-4-6", "claude-haiku-4-5-20251001"
  Gemini    : "gemini/gemini-1.5-pro", "gemini/gemini-2.0-flash"
  OpenAI    : "gpt-4o", "gpt-4o-mini"
"""
import os
import litellm
from agent_bazaar.config import settings

litellm.drop_params = True   # silently ignore params unsupported by a provider
litellm.suppress_debug_info = True

# Push API keys into env so LiteLLM can find them
if settings.anthropic_api_key:
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
if settings.gemini_api_key:
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)


async def complete(model: str, system: str, user: str, max_tokens: int = 2048) -> tuple[str, object]:
    """Call any LiteLLM-supported model. Returns (text, response)."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    response = await litellm.acompletion(model=model, messages=messages, max_tokens=max_tokens)
    text = response.choices[0].message.content or ""
    return text.strip(), response
