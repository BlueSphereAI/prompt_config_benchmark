# Quick Start Guide

This guide will help you get started with the Prompt Configuration Benchmark Framework in just a few minutes.

## Installation (5 minutes)

1. **Install the framework:**
   ```bash
   pip install -e .
   ```

2. **Initialize the environment:**
   ```bash
   benchmark init
   ```

   This creates:
   - Example prompts in `data/prompts/`
   - Example configurations in `data/configs/`
   - Directory structure for results

3. **Configure your API key:**

   Edit the `.env` file and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

## Your First Benchmark (2 minutes)

1. **Run experiments:**
   ```bash
   benchmark run
   ```

   This runs all example prompts with all example configurations and stores the results.

2. **View the results:**
   ```bash
   benchmark analyze
   ```

   This shows you which configurations performed best for each prompt.

## Evaluate Results (Optional)

### AI Evaluation (Automated)

Let an LLM score the results automatically:

```bash
benchmark ai-evaluate
```

Then view the updated analysis:

```bash
benchmark analyze
```

### Human Evaluation (Interactive)

Manually score and provide feedback:

```bash
benchmark evaluate --evaluator "Your Name"
```

You'll be guided through each result with an interactive interface.

## Creating Your Own Tests

### Create a Custom Prompt

Create `data/prompts/my-task.yaml`:

```yaml
name: my-task
template: "Explain {concept} in simple terms suitable for a {audience}."
description: Explain concepts to different audiences
category: education
tags:
  - explanation
  - education
variables:
  concept: "quantum computing"
  audience: "high school student"
```

### Create a Custom Configuration

Create `data/configs/my-config.json`:

```json
{
  "model": "gpt-4-turbo-preview",
  "temperature": 0.5,
  "max_output_tokens": 1000
}
```

### Run Your Custom Test

```bash
benchmark run --prompt my-task --config my-config
```

## Understanding the Results

After running experiments and evaluations, the analyzer shows:

- **Best by Score**: Which config got the highest average evaluation scores
- **Best by Speed**: Which config was fastest
- **Best by Cost**: Which config was most cost-effective
- **Detailed Stats**: Average duration, tokens used, costs, etc.

## Export Data

Export all results to CSV for analysis in Excel or other tools:

```bash
benchmark analyze --export my-results.csv
```

## Next Steps

1. **Create prompts** for your actual use cases
2. **Define configurations** you want to test (different models, temperatures, etc.)
3. **Run experiments** to gather data
4. **Evaluate results** (AI or human)
5. **Analyze** to find the best configuration for each use case

## Common Workflows

### Workflow 1: Quick Comparison

```bash
# Test 2-3 configs on one prompt
benchmark run --prompt summarize --config gpt4-fast --config gpt4-balanced

# AI evaluate
benchmark ai-evaluate --prompt summarize

# See results
benchmark analyze --prompt summarize
```

### Workflow 2: Comprehensive Testing

```bash
# Run everything
benchmark run

# Get AI evaluations
benchmark ai-evaluate

# Add human evaluations for important prompts
benchmark evaluate --prompt critical-task --evaluator "QA Team"

# Full analysis with export
benchmark analyze --export full-report.csv
```

### Workflow 3: Iterative Testing

```bash
# Test initial configs
benchmark run

# Analyze
benchmark analyze

# Add new config based on findings
# Edit data/configs/optimized.json

# Test new config
benchmark run --config optimized

# Compare
benchmark analyze
```

## Tips

- Start with a small set of prompts and configs to test the workflow
- Use AI evaluation for quick feedback, human evaluation for quality checks
- Export to CSV to do deeper analysis in pandas or Excel
- Keep your `.env` file secure (it contains your API key)
- Check `data/results/benchmark.db` to see all stored data

## Getting Help

- Read the full [README.md](README.md) for detailed documentation
- Check example files in `data/prompts/` and `data/configs/`
- Review test files in `tests/` for code examples

## Cost Considerations

The framework estimates costs based on token usage. To minimize costs during testing:

1. Use smaller `max_output_tokens` values
2. Test with `gpt-3.5-turbo` or `gpt-4o-mini` first
3. Use a small subset of prompts initially
4. Check estimated costs in the analysis before scaling up

Example cost-conscious config:

```json
{
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_output_tokens": 500
}
```
