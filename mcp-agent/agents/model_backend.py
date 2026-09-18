"""
Single seam for model calls, so orchestrator.py doesn't care whether it's
talking to Claude or a local Ollama model. Controlled by the MODEL_BACKEND
env var: "anthropic" (default) or "ollama".

This is the whole point of the abstraction: the multi-agent flow shape
(Planner -> Researcher -> Writer) and the MCP tool-calling logic stay
completely identical either way. Only this file changes.
"""
import os
import httpx
from anthropic import Anthropic

MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "anthropic")

# Anthropic setup (only used if MODEL_BACKEND == "anthropic")
_anthropic_client = None
if MODEL_BACKEND == "anthropic":
    _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# Ollama setup (only used if MODEL_BACKEND == "ollama")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


def call_model(prompt: str, max_tokens: int = 500) -> str:
    """Send a single-turn prompt to whichever backend is configured and
    return the plain text response. Same signature regardless of backend —
    this is what keeps orchestrator.py backend-agnostic."""
    if MODEL_BACKEND == "ollama":
        return _call_ollama(prompt, max_tokens)
    return _call_anthropic(prompt, max_tokens)


def _call_anthropic(prompt: str, max_tokens: int) -> str:
    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _call_ollama(prompt: str, max_tokens: int) -> str:
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        return f"[ollama call failed: {e}]"
