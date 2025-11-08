# Prompt Configuration Benchmark Framework

A comprehensive Python framework for testing and comparing different LLM configurations across various prompts. This tool helps you systematically evaluate which OpenAI model configurations work best for your specific use cases.

## Features

- **Systematic Testing**: Run experiments with multiple prompts and configurations
- **Langfuse Format**: Store configurations in the Langfuse format (model, temperature, max_output_tokens, etc.)
- **Comprehensive Metrics**: Track response time, token usage, and estimated costs
- **Dual Evaluation**: Support for both human and AI-based evaluation of results
- **Statistical Analysis**: Compare configurations to find the best performers
- **SQLite Storage**: Persistent storage with easy export to CSV/JSON
- **CLI Interface**: User-friendly command-line tools

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd prompt_config_benchmark
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Initialize the environment:
```bash
benchmark init
```

5. Configure your API key in `.env`:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Quick Start

### 1. Initialize the Environment

```bash
benchmark init
```

This creates:
- `data/prompts/` - Example prompt definitions
- `data/configs/` - Example Langfuse configurations
- `data/results/` - Directory for results database
- `.env` - Environment configuration file

### 2. Run Benchmarks

Run all prompts with all configurations:

```bash
benchmark run
```

Run specific prompts or configurations:

```bash
# Run specific prompts
benchmark run --prompt summarize --prompt creative-story

# Run specific configs
benchmark run --config gpt4-balanced --config gpt35-fast

# Combine filters
benchmark run --prompt summarize --config gpt4-balanced
```

### 3. Evaluate Results

#### Human Evaluation

Interactively evaluate results:

```bash
benchmark evaluate
```

Evaluate specific prompt:

```bash
benchmark evaluate --prompt summarize --evaluator "Your Name"
```

With custom criteria:

```bash
benchmark evaluate --criteria accuracy --criteria relevance --criteria coherence
```

#### AI Evaluation

Use an LLM to automatically evaluate:

```bash
benchmark ai-evaluate
```

Specify evaluation model:

```bash
benchmark ai-evaluate --model gpt-4 --prompt summarize
```

### 4. Analyze Results

View analysis for all prompts:

```bash
benchmark analyze
```

Analyze specific prompt:

```bash
benchmark analyze --prompt summarize
```

Export to CSV:

```bash
benchmark analyze --export results.csv
```

## Configuration Format

### Langfuse Configuration

Configurations use the Langfuse JSON format:

```json
{
  "model": "gpt-4-turbo-preview",
  "temperature": 0.7,
  "max_output_tokens": 1500,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

For GPT-5 models (extended format):

```json
{
  "model": "gpt-5",
  "max_output_tokens": 2000,
  "verbosity": "medium",
  "reasoning_effort": "high"
}
```

Save configurations as JSON files in `data/configs/`.

### Prompt Definitions

Prompts are defined in YAML format:

```yaml
name: summarize
template: "Please summarize the following text concisely:\n\n{text}"
description: Summarize a given text
category: text-processing
tags:
  - summarization
  - text
variables:
  text: ""
```

Save prompts as YAML files in `data/prompts/`.

## Project Structure

```
prompt_config_benchmark/
├── src/
│   └── prompt_benchmark/
│       ├── __init__.py
│       ├── models.py              # Pydantic data models
│       ├── config_loader.py       # Load configs and prompts
│       ├── executor.py            # Run experiments
│       ├── storage.py             # SQLite database
│       ├── evaluator.py           # Human & AI evaluation
│       ├── analyzer.py            # Statistical analysis
│       └── cli.py                 # Command-line interface
├── tests/                         # Unit tests
├── data/
│   ├── prompts/                   # Prompt definitions
│   ├── configs/                   # Configuration files
│   └── results/                   # Results database
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Usage Examples

### Creating Custom Configurations

Create a configuration file `data/configs/my-config.json`:

```json
{
  "model": "gpt-4",
  "temperature": 0.5,
  "max_output_tokens": 2000
}
```

### Creating Custom Prompts

Create a prompt file `data/prompts/my-prompt.yaml`:

```yaml
name: my-prompt
template: "Write a {style} description of {topic}"
description: Generate descriptions
category: creative
tags:
  - creative
  - description
variables:
  style: "technical"
  topic: "artificial intelligence"
```

### Running a Full Benchmark Suite

```bash
# 1. Create your prompts and configs
benchmark init

# 2. Run all experiments
benchmark run

# 3. Evaluate with AI
benchmark ai-evaluate

# 4. Add human evaluations
benchmark evaluate --evaluator "Team Lead"

# 5. Analyze and export
benchmark analyze --export results.csv
```

### Programmatic Usage

You can also use the framework programmatically:

```python
from prompt_benchmark.config_loader import ConfigLoader, PromptLoader
from prompt_benchmark.executor import ExperimentExecutor
from prompt_benchmark.storage import ResultStorage
from prompt_benchmark.analyzer import BenchmarkAnalyzer

# Load configurations
config = ConfigLoader.load_config_from_file("data/configs/gpt4-balanced.json")
prompt = PromptLoader.load_prompt_from_file("data/prompts/summarize.yaml")

# Initialize components
storage = ResultStorage()
executor = ExperimentExecutor()

# Run experiment
result = executor.run_experiment(
    prompt=prompt,
    config=config,
    config_name="gpt4-balanced"
)

# Save result
storage.save_result(result)

# Analyze
analyzer = BenchmarkAnalyzer(storage)
comparison = analyzer.analyze_prompt("summarize")
analyzer.print_comparison(comparison)
```

## Metrics Tracked

For each experiment, the framework tracks:

- **Timing**: Total duration in seconds
- **Token Usage**: Prompt tokens, completion tokens, total tokens
- **Cost**: Estimated cost in USD (based on current pricing)
- **Response**: Full LLM response text
- **Configuration**: Complete configuration used
- **Success/Failure**: Whether the request succeeded
- **Errors**: Any error messages

## Evaluation

### Human Evaluation

The human evaluation interface guides you through:

1. Viewing the prompt and response
2. Providing an overall score (0-10)
3. Scoring individual criteria (optional)
4. Adding written feedback (strengths, weaknesses, notes)

### AI Evaluation

AI evaluation uses an LLM as a judge to score responses based on:

- Accuracy
- Relevance
- Coherence
- Completeness

You can customize the evaluation criteria and prompt.

## Analysis and Reporting

The analyzer provides:

- **Best by Score**: Highest average evaluation score
- **Best by Speed**: Fastest average response time
- **Best by Cost**: Lowest average cost
- **Detailed Statistics**: Per-config averages and totals
- **Export Options**: CSV, JSON for further analysis

## Environment Variables

Configure in `.env`:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DATABASE_URL=sqlite:///data/results/benchmark.db
DEFAULT_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1500

# AI Evaluator
EVALUATOR_MODEL=gpt-4
EVALUATOR_TEMPERATURE=0.3
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=prompt_benchmark --cov-report=html
```

## Development

### Code Style

The project uses:
- Black for code formatting
- Ruff for linting

Format code:
```bash
black src/ tests/
```

Lint:
```bash
ruff check src/ tests/
```

### Contributing

1. Create a feature branch
2. Add tests for new functionality
3. Ensure all tests pass
4. Format and lint code
5. Submit a pull request

## Cost Estimation

The framework tracks estimated costs based on current OpenAI pricing. Costs are calculated using:

- Model-specific pricing per 1M tokens
- Actual token counts from API responses
- Separate input/output token pricing

Note: Pricing is updated periodically but may not reflect the latest changes. Check `executor.py` for current pricing table.

## Advanced Features

### Batch Processing

Run multiple prompts with multiple configs:

```python
executor = ExperimentExecutor()
results = executor.run_full_benchmark(
    prompts=prompts_dict,
    configs=configs_dict
)
```

### Custom Evaluation Criteria

```bash
benchmark evaluate \
  --criteria accuracy \
  --criteria relevance \
  --criteria creativity \
  --criteria coherence
```

### Data Export

```python
analyzer = BenchmarkAnalyzer(storage)
df = analyzer.export_to_dataframe()
df.to_csv("full_results.csv")
```

## Troubleshooting

### API Key Issues

```
Error: OpenAI API key not provided
```
→ Ensure `OPENAI_API_KEY` is set in `.env`

### No Results to Evaluate

```
Found 0 unevaluated results
```
→ Run `benchmark run` first to generate results

### Database Errors

→ Delete `data/results/benchmark.db` and rerun experiments

## Roadmap

Future enhancements:

- [ ] Support for more LLM providers (Anthropic, Google)
- [ ] Web UI for evaluation and analysis
- [ ] Async/parallel experiment execution
- [ ] Advanced statistical analysis
- [ ] Experiment templates and presets
- [ ] Integration with Langfuse cloud

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review example configurations

## Acknowledgments

- Built with Pydantic for data validation
- Uses SQLAlchemy for database management
- CLI powered by Click and Rich
- Inspired by Langfuse configuration format
