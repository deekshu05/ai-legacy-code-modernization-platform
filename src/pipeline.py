"""End-to-end orchestration: parse -> analyze -> transform -> validate -> track.

Usage:
    python -m src.pipeline --target-path ./path/to/legacy/project
"""

from __future__ import annotations

import argparse
import sys

from src.ast_parser import analyze_directory
from src.code_transformer import apply_transformation
from src.config import PipelineConfig
from src.llm_analyzer import analyze_finding, build_client
from src.mlops.tracking import (
    configure_langsmith,
    log_run_summary,
    log_transform_result,
    mlflow_run,
)


def run_pipeline(config: PipelineConfig) -> dict:
    configure_langsmith(config)
    client = build_client(
        provider=config.llm_provider,
        model=config.llm_model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    findings = analyze_directory(config.target_path, config.file_extensions)
    print(f"Found {len(findings)} legacy pattern(s) in {config.target_path}")

    results = []
    with mlflow_run(config):
        for finding in findings:
            suggestion = analyze_finding(finding, client)
            result = apply_transformation(suggestion, dry_run=config.dry_run)
            log_transform_result(result)
            results.append(result)

            status = "applied" if result.applied else ("invalid" if not result.valid_syntax else "dry-run")
            print(f"[{status}] {finding.file_path}:{finding.line} — {finding.pattern}")

        summary = log_run_summary(results)

    print("\nRun summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-powered legacy code modernization pipeline")
    parser.add_argument("--target-path", required=True, help="Path to the codebase to modernize")
    parser.add_argument("--dry-run", action="store_true", help="Validate suggestions without writing changes")
    args = parser.parse_args()

    config = PipelineConfig(target_path=args.target_path, dry_run=args.dry_run)
    run_pipeline(config)


if __name__ == "__main__":
    sys.exit(main())
