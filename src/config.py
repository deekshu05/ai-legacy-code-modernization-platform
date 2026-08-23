"""Configuration for the legacy code modernization pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """Runtime configuration for a modernization pipeline run."""

    target_path: str
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    # MLOps
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    mlflow_experiment_name: str = os.getenv(
        "MLFLOW_EXPERIMENT_NAME", "legacy-code-modernization"
    )
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "legacy-code-modernization")

    # Validation
    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".py",))
