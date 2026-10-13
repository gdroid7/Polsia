"""Abstract base class for all Polsia AI agents."""
import json
import os
import subprocess
import time
from abc import ABC, abstractmethod

from app.config import settings


class BasePolsiaAgent(ABC):
    agent_type: str = "base"

    def call_claude(self, prompt: str) -> str:
        """Call Claude CLI or return mock response if CLAUDE_CLI_MOCK is set."""
        if os.getenv("CLAUDE_CLI_MOCK", "").lower() in ("true", "1", "yes"):
            raw = os.getenv("CLAUDE_CLI_MOCK_RESPONSE", settings.claude_cli_mock_response)
            return json.loads(raw)["result"]

        result = subprocess.run(
            [settings.claude_cli_path, "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return json.loads(result.stdout)["result"]

    def call_claude_json(self, prompt: str) -> dict:
        """Call Claude and parse the result string as JSON."""
        raw = self.call_claude(prompt)
        return json.loads(raw)

    def timed_run(self, task: dict, context: dict) -> dict:
        """Run the agent and attach duration_secs to the result."""
        start = time.monotonic()
        result = self.run(task, context)
        duration = round(time.monotonic() - start, 3)
        return {**result, "duration_secs": duration}

    @abstractmethod
    def run(self, task: dict, context: dict) -> dict:
        """Implement in subclass. Must return dict with at least {'summary': str}."""
        ...
