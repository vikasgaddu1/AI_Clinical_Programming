"""
LLM Client: wraps the Anthropic Claude API for agent use.

Provides a unified interface for all agents to call Claude models.
Supports three modes:
  - LIVE:    Calls the Anthropic API (requires ANTHROPIC_API_KEY)
  - DRY_RUN: Logs prompts to file without calling API (for training without keys)
  - OFF:     Uses template/rule-based logic only (no LLM involvement)

The mode is controlled by config.yaml:
  agents:
    use_llm: true       # false = OFF mode
    dry_run: false       # true = DRY_RUN mode (overrides use_llm)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client for all orchestrator agents."""

    def __init__(
        self,
        agent_config: Optional[Dict[str, Any]] = None,
        log_dir: Optional[str] = None,
    ) -> None:
        self._config = agent_config or {}
        self._use_llm = self._config.get("use_llm", False)
        self._dry_run = self._config.get("dry_run", False)
        self._client = None
        self._log_dir = Path(log_dir) if log_dir else None

        if self._log_dir:
            self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def mode(self) -> str:
        """Return the current mode: LIVE, DRY_RUN, or OFF."""
        if self._dry_run:
            return "DRY_RUN"
        if self._use_llm:
            return "LIVE"
        return "OFF"

    def _get_client(self):
        """Lazily initialise the Anthropic client."""
        if self._client is not None:
            return self._client

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            # Try reading from .env file in project root
            env_path = Path(__file__).resolve().parent.parent.parent / ".env"
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not found. Set it in the environment or in a .env file "
                "at the project root. Alternatively, set use_llm: false in config.yaml."
            )

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
            return self._client
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            )

    def _log_interaction(
        self,
        agent_name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        mode: str,
    ) -> None:
        """Write a timestamped log entry for the interaction."""
        if not self._log_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self._log_dir / f"{agent_name}_{timestamp}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "model": model,
            "mode": mode,
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt),
            "response_length": len(response_text),
            "system_prompt": system_prompt[:2000] + ("..." if len(system_prompt) > 2000 else ""),
            "user_prompt": user_prompt[:2000] + ("..." if len(user_prompt) > 2000 else ""),
            "response": response_text[:5000] + ("..." if len(response_text) > 5000 else ""),
        }
        log_file.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        logger.info("LLM interaction logged to %s", log_file)

    def call_agent(
        self,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Call an LLM agent and return the response text.

        In DRY_RUN mode, logs the prompts and returns a placeholder.
        In OFF mode, returns an empty string (caller should use template logic).

        Parameters:
            agent_name:    Name of the calling agent (for logging)
            system_prompt: System instructions for the model
            user_prompt:   The user-facing prompt with context
            model:         Model ID (e.g. 'claude-sonnet-4-20250514')
            max_tokens:    Maximum response tokens
        """
        # Resolve model from config if not provided
        if model is None:
            agent_cfg = self._config.get(agent_name, {})
            model = agent_cfg.get("model", "claude-sonnet-4-20250514")

        # OFF mode — no LLM, return empty for template fallback
        if self.mode == "OFF":
            logger.info("[%s] LLM mode OFF — using template logic", agent_name)
            return ""

        # DRY_RUN mode — log prompts, return placeholder
        if self.mode == "DRY_RUN":
            placeholder = (
                f"[DRY_RUN] Agent '{agent_name}' would call model '{model}' "
                f"with {len(system_prompt)} char system prompt and "
                f"{len(user_prompt)} char user prompt."
            )
            self._log_interaction(
                agent_name, model, system_prompt, user_prompt, placeholder, "DRY_RUN"
            )
            logger.info("[%s] DRY_RUN — prompts logged, no API call", agent_name)
            return placeholder

        # LIVE mode — call the API
        client = self._get_client()
        logger.info("[%s] Calling %s (max_tokens=%d)", agent_name, model, max_tokens)

        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = ""
        for block in message.content:
            if hasattr(block, "text"):
                response_text += block.text

        self._log_interaction(
            agent_name, model, system_prompt, user_prompt, response_text, "LIVE"
        )
        return response_text

    def get_model_for_agent(self, agent_name: str) -> str:
        """Return the configured model ID for a given agent."""
        agent_cfg = self._config.get(agent_name, {})
        return agent_cfg.get("model", "claude-sonnet-4-20250514")

    def is_available(self) -> bool:
        """Return True if the LLM client can make API calls."""
        if self.mode != "LIVE":
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False
