# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python framework for systematically testing and comparing different OpenAI LLM configurations (specifically GPT-5 variants) across various prompts. Uses Langfuse configuration format and OpenAI messages format for prompts.

## Essential Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Initialize project structure
benchmark init
```

### Running Benchmarks
```bash
# Run all experiments (all prompts × all configs)
benchmark run

# Run specific prompt or config
benchmark run --prompt re-organize-idea-wooden-puzzle --config gpt5-standard

# Run with custom directories
benchmark run --prompts-dir data/prompts --configs-dir data/configs
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=prompt_benchmark --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Database Operations
```bash
# Results stored in SQLite at: data/results/benchmark.db
# Delete database to reset: rm data/results/benchmark.db

# Access database directly
sqlite3 data/results/benchmark.db "SELECT * FROM experiment_results"
```

## Architecture

### Data Flow
1. **Config & Prompt Loading** (`config_loader.py`) → Load JSON configs and prompts from filesystem
2. **Execution** (`executor.py`) → Run experiments via OpenAI API with AsyncOpenAI for parallel execution
3. **Storage** (`storage.py`) → Persist results to SQLite using SQLAlchemy
4. **Evaluation** (`evaluator.py`) → Score results (human or AI)
5. **Analysis** (`analyzer.py`) → Compare configs and generate reports

### Key Design Patterns

**Langfuse Config Format** (JSON):
- `model`: Model ID (e.g., "gpt-5", "gpt-5-mini")
- `max_output_tokens`: Token limit for completion
- `verbosity`: "low" | "medium" | "high" (GPT-5 specific)
- `reasoning_effort`: "minimal" | "medium" | "high" (GPT-5 specific)
- `temperature`, `top_p`, `frequency_penalty`, `presence_penalty` (optional)

**OpenAI Messages Format** (JSON):
- Prompts are arrays of message objects: `[{"role": "system"|"user"|"assistant", "content": "..."}]`
- Can be bare array or wrapped in object with metadata

**Parallel Execution**:
- Uses `AsyncOpenAI` client with `asyncio.gather()` for concurrent API calls
- `run_batch()` executes all configs for a prompt in parallel
- `run_batch_async()` is the underlying async implementation

### GPT-5 Critical Details

**Token Parameter**:
- GPT-5 requires `max_completion_tokens` parameter (NOT `max_tokens`)
- Handled in `executor.py:_prepare_api_params()` with model name check

**Reasoning Tokens**:
- GPT-5 uses internal reasoning that consumes tokens from `max_completion_tokens` budget
- `completion_tokens_details.reasoning_tokens` shows internal reasoning usage
- All tokens (reasoning + output) count toward the limit
- **Important**: Token limits must be 2-3x higher than other models to account for reasoning overhead
- Empty responses with `finish_reason: length` indicate reasoning consumed entire budget

**Unsupported Parameters**:
- GPT-5 does NOT support `temperature` parameter
- `verbosity` and `reasoning_effort` are stored in config but NOT currently sent to API (TODO in executor.py lines 254-259)

### Models (`models.py`)

**LangfuseConfig**: Configuration with validation (Pydantic)
**Prompt**: Messages array with metadata
**ExperimentResult**: API response + metrics + timing
**Evaluation**: Human/AI scoring of results

All use Pydantic for validation and serialization.

### Executor (`executor.py`)

**Critical Methods**:
- `run_experiment()`: Synchronous single experiment
- `run_experiment_async()`: Async single experiment
- `run_batch()` / `run_batch_async()`: Parallel execution of multiple configs on same prompt
- `run_full_benchmark()` / `run_full_benchmark_async()`: All prompts × all configs

**Timing**: Uses `time.perf_counter()` for duration and `datetime.utcnow()` for timestamps

**Cost Estimation**: Based on `MODEL_PRICING` dict (per 1M tokens) at top of file

### Storage (`storage.py`)

**Database Schema**:
- `experiment_results`: Results with JSON-serialized config and metadata
- `evaluations`: Human/AI evaluations linked by `experiment_id`

**Key Methods**:
- `save_result()`: Persist ExperimentResult
- `get_results_by_prompt()`: Filter by prompt name
- `save_evaluation()`: Persist Evaluation

### CLI (`cli.py`)

Entry point is `benchmark` command with subcommands:
- `init`: Setup directories and example files
- `run`: Execute experiments
- `evaluate`: Human evaluation interface
- `ai-evaluate`: AI-based evaluation
- `analyze`: Compare configs and export

## Configuration Files

### Current GPT-5 Configs (`data/configs/`)

All configs updated with high token limits due to reasoning overhead:
- `gpt5-mini-fast`: 2000 tokens
- `gpt5-mini-balanced`: 3000 tokens
- `gpt5-minimal`: 2500 tokens
- `gpt5-concise`: 8000 tokens
- `gpt5-compact`: 8000 tokens
- `gpt5-standard`: 8000 tokens
- `gpt5-balanced-high-reasoning`: 5000 tokens
- `gpt5-detailed`: 5000 tokens
- `gpt5-verbose`: 10000 tokens
- `gpt5-thorough`: 8000 tokens
- `gpt5-extended`: 10000 tokens

**Token Limits Rationale**: These are 2-3x higher than original values because GPT-5 reasoning tokens consume significant portion of the budget before generating output.

## Common Issues

### Empty Responses with `finish_reason: length`
- Cause: GPT-5 reasoning consumed all tokens in `max_completion_tokens` budget
- Fix: Increase `max_output_tokens` in config (typically 8000+ for GPT-5)

### Parameter Error: `max_tokens` not supported
- Cause: Using wrong parameter for GPT-5
- Fix: Use `max_completion_tokens` (handled automatically in executor.py)

### Experiments Running Serially
- Cause: Not using `run_batch()` method
- Fix: Use `executor.run_batch()` which calls `run_batch_async()` internally

### Missing Dependencies
- Cause: Virtual environment not activated or dependencies not installed
- Fix: `source venv/bin/activate && pip install -e .`

## Environment Variables

`.env` file (required):
```
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///data/results/benchmark.db  # Optional
```
