"""LLMOps observability: MLflow experiment tracking + LangSmith tracing.

Every pipeline run logs prompt/response metadata, latency, token usage,
and validation outcomes so transformation quality and cost can be
monitored over time and across model/prompt versions.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import asdict
from typing import Iterator

import mlflow

from src.code_transformer import TransformResult
from src.config import PipelineConfig


@contextmanager
def mlflow_run(config: PipelineConfig) -> Iterator[None]:
    mlflow.set_tracking_uri(config.mlflow_tracking_uri)
    mlflow.set_experiment(config.mlflow_experiment_name)
    with mlflow.start_run():
        mlflow.log_params(
            {
                "llm_provider": config.llm_provider,
                "llm_model": config.llm_model,
                "temperature": config.temperature,
                "target_path": config.target_path,
                "dry_run": config.dry_run,
            }
        )
        yield


def log_transform_result(result: TransformResult) -> None:
    """Log a single transformation's outcome as MLflow metrics/params."""
    suggestion = result.suggestion
    mlflow.log_metrics(
        {
            "latency_ms": suggestion.latency_ms,
            "input_tokens": suggestion.input_tokens,
            "output_tokens": suggestion.output_tokens,
            "total_tokens": suggestion.input_tokens + suggestion.output_tokens,
            "valid_syntax": int(result.valid_syntax),
            "applied": int(result.applied),
        }
    )


def log_run_summary(results: list[TransformResult]) -> dict:
    """Aggregate and log run-level metrics; return the summary dict."""
    total = len(results)
    applied = sum(1 for r in results if r.applied)
    valid = sum(1 for r in results if r.valid_syntax)
    total_tokens = sum(r.suggestion.input_tokens + r.suggestion.output_tokens for r in results)
    avg_latency = sum(r.suggestion.latency_ms for r in results) / total if total else 0.0

    summary = {
        "total_findings": total,
        "transformation_success_rate": applied / total if total else 0.0,
        "code_validation_accuracy": valid / total if total else 0.0,
        "avg_latency_ms": avg_latency,
        "total_tokens_used": total_tokens,
    }
    mlflow.log_metrics(summary)
    return summary


def is_langsmith_enabled() -> bool:
    return bool(os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY"))


def configure_langsmith(config: PipelineConfig) -> None:
    """Enable LangSmith tracing for the run, if credentials are present."""
    if not is_langsmith_enabled():
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = config.langsmith_project
