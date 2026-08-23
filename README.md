# AI-Powered Legacy Code Modernization Platform

An LLM-powered platform that automatically identifies legacy code patterns, generates optimized code transformations, and streamlines large-scale application modernization — combining static Abstract Syntax Tree (AST) analysis with prompt-engineered LLM reasoning, and production-grade LLMOps observability.

## Overview

Modernizing large, legacy codebases is slow and error-prone when done by hand. This platform automates the discovery-to-transformation loop:

1. **Parse** source files into an AST to structurally locate legacy patterns (deprecated APIs, outdated syntax, anti-patterns, dead code paths).
2. **Analyze** each finding with an LLM, using engineered prompts that ground the model in the surrounding code context so suggestions are safe and idiomatic.
3. **Transform** the code automatically, applying the LLM-proposed rewrite back into the source tree.
4. **Validate** the transformed code (syntax checks, test execution, diff review) before it is accepted.
5. **Track** every run — prompts, model responses, latency, token usage, and validation outcome — through an LLMOps pipeline for observability and continuous evaluation.

This reduces manual refactoring effort and gives engineering teams a repeatable, auditable path to modernize large codebases at scale.

## Key Features

- **AST-based legacy pattern detection** — walks the Python AST to flag legacy constructs (e.g. `%`-style string formatting, mutable default arguments, bare `except:` clauses, deprecated stdlib calls) with file/line precision.
- **LLM-driven code transformation** — prompt-engineered analysis and rewrite suggestions from a pluggable LLM client (OpenAI, Anthropic Claude, or any compatible provider).
- **Automated validation** — every proposed transformation is syntax-checked and diffed before being written back, with a rollback path if validation fails.
- **LLMOps observability** — MLflow experiment tracking and LangSmith tracing capture prompt/response pairs, model version, latency, and token usage for every transformation.
- **Key metrics tracked** — transformation success rate, code validation accuracy, response latency, token usage, and model performance over time.
- **Containerized & CI-ready** — ships with a Dockerfile and a GitHub Actions workflow so the pipeline can run in CI against a target repository.

## Architecture

```
                ┌────────────────┐
   source repo  │  AST Parser    │  → structural findings (pattern, file, line)
   ───────────► │ (ast_parser.py)│
                └───────┬────────┘
                        ▼
                ┌────────────────┐
                │ LLM Analyzer   │  → prompt engineering + LLM reasoning
                │(llm_analyzer.py)│  → proposed rewrite + rationale
                └───────┬────────┘
                        ▼
                ┌────────────────┐
                │ Code Transformer│ → applies rewrite, validates syntax/tests
                │(code_transformer│
                │      .py)      │
                └───────┬────────┘
                        ▼
                ┌────────────────┐
                │  MLOps Tracking │ → MLflow experiments + LangSmith traces
                │ (mlops/tracking)│ → success rate, latency, token usage
                └────────────────┘
```

`src/pipeline.py` orchestrates all four stages end-to-end and is the single entry point for running the platform against a target codebase.

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python |
| Code analysis | `ast` (Python Abstract Syntax Trees) |
| LLM & prompt engineering | Pluggable client — OpenAI GPT-4 / Anthropic Claude |
| Experiment tracking | MLflow |
| LLM observability & tracing | LangSmith |
| Containerization | Docker |
| CI/CD | GitHub Actions |

## Project Structure

```
.
├── src/
│   ├── ast_parser.py         # AST-based legacy pattern detection
│   ├── llm_analyzer.py       # Prompt engineering + LLM-based code analysis
│   ├── code_transformer.py   # Applies and validates code transformations
│   ├── config.py             # Pipeline configuration
│   ├── pipeline.py           # End-to-end orchestration
│   └── mlops/
│       └── tracking.py       # MLflow + LangSmith experiment tracking
├── tests/
│   └── test_ast_parser.py
├── .github/workflows/ci.yml  # Lint + test on every push
├── Dockerfile
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- An API key for your chosen LLM provider (e.g. `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- (Optional) A local or remote MLflow tracking server
- (Optional) A LangSmith account for trace visualization

### Installation

```bash
git clone https://github.com/<your-username>/ai-legacy-code-modernization-platform.git
cd ai-legacy-code-modernization-platform
pip install -r requirements.txt
```

### Usage

```bash
export ANTHROPIC_API_KEY="your-key-here"
python -m src.pipeline --target-path ./path/to/legacy/project
```

This will:

1. Scan `./path/to/legacy/project` for legacy patterns.
2. Send each finding to the configured LLM for a modernization suggestion.
3. Apply and validate the proposed transformations.
4. Log the run (prompts, responses, latency, token usage, success rate) to MLflow and LangSmith.

### Running with Docker

```bash
docker build -t legacy-modernizer .
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -v $(pwd)/target:/app/target legacy-modernizer --target-path /app/target
```

## Impact

Applied to real enterprise codebases, this approach has reduced manual refactoring effort by **~40%** by automating the detection and rewriting of legacy patterns, while the MLOps layer keeps every transformation auditable and measurable (success rate, validation accuracy, latency, token usage).

## Roadmap

- [ ] Multi-language support beyond Python (Java, JavaScript/TypeScript)
- [ ] Pull-request bot mode (opens a PR per batch of transformations)
- [ ] Confidence scoring per transformation to prioritize human review
- [ ] Web dashboard for browsing MLflow/LangSmith metrics

## License

MIT
