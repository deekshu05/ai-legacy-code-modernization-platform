"""LLM-driven analysis of legacy-pattern findings.

Uses prompt engineering to turn a structural AST finding into a concrete,
context-aware modernization suggestion. The LLM client is pluggable so the
same pipeline can run against Anthropic Claude, OpenAI, or a mock client
for tests.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from src.ast_parser import Finding

SYSTEM_PROMPT = """You are a senior software engineer specializing in code \
modernization. You are given a legacy code pattern found via static AST \
analysis, along with its surrounding context. Propose a minimal, safe, \
idiomatic rewrite that preserves behavior exactly. Respond with the \
rewritten code only, followed by a one-sentence rationale prefixed with \
'RATIONALE:'.
"""

USER_PROMPT_TEMPLATE = """Pattern: {pattern}
Description: {description}
File: {file_path} (line {line})

Original snippet:
```python
{snippet}
```

Rewrite this snippet to remove the legacy pattern while preserving behavior.
"""


@dataclass
class Suggestion:
    finding: Finding
    rewritten_code: str
    rationale: str
    latency_ms: float
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    """Minimal interface any LLM provider client must implement."""

    def complete(self, system: str, user: str) -> tuple[str, int, int]:
        """Return (completion_text, input_tokens, output_tokens)."""
        ...


class AnthropicClient:
    """Thin wrapper around the Anthropic Claude API."""

    def __init__(self, model: str, max_tokens: int = 2048, temperature: float = 0.1):
        import anthropic  # imported lazily so the package is optional at import time

        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def complete(self, system: str, user: str) -> tuple[str, int, int]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return text, response.usage.input_tokens, response.usage.output_tokens


class MockClient:
    """Deterministic client for local testing without an API key."""

    def complete(self, system: str, user: str) -> tuple[str, int, int]:
        return (
            "# modernized automatically\n" + user.split("```python\n")[-1].split("```")[0]
            + "\nRATIONALE: Replaced legacy pattern with a modern equivalent (mock).",
            len(user.split()),
            12,
        )


def build_client(provider: str, model: str, max_tokens: int, temperature: float) -> LLMClient:
    if provider == "anthropic":
        return AnthropicClient(model=model, max_tokens=max_tokens, temperature=temperature)
    if provider == "mock":
        return MockClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")


def analyze_finding(finding: Finding, client: LLMClient) -> Suggestion:
    """Ask the LLM to propose a modernized rewrite for a single finding."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        pattern=finding.pattern,
        description=finding.description,
        file_path=finding.file_path,
        line=finding.line,
        snippet=finding.snippet,
    )

    start = time.perf_counter()
    completion, input_tokens, output_tokens = client.complete(SYSTEM_PROMPT, user_prompt)
    latency_ms = (time.perf_counter() - start) * 1000

    code, _, rationale = completion.partition("RATIONALE:")
    return Suggestion(
        finding=finding,
        rewritten_code=code.strip(),
        rationale=rationale.strip() or "No rationale provided.",
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
