# GPT-5 Configuration Guide

This directory contains pre-configured GPT-5 settings optimized for different use cases. Each configuration tests different combinations of verbosity, reasoning effort, and output length.

## Configuration Overview

| Config Name | Model | Tokens | Verbosity | Reasoning | Best For |
|-------------|-------|--------|-----------|-----------|----------|
| **gpt5-mini-fast** | gpt-5-mini | 500 | low | minimal | Quick drafts, simple tasks, cost-sensitive |
| **gpt5-mini-balanced** | gpt-5-mini | 1000 | medium | medium | General purpose, balanced cost/quality |
| **gpt5-minimal** | gpt-5 | 600 | low | minimal | Fast responses, simple answers |
| **gpt5-concise** | gpt-5 | 800 | low | medium | Brief but thoughtful responses |
| **gpt5-compact** | gpt-5 | 600 | low | high | Deep thinking, concise output |
| **gpt5-standard** | gpt-5 | 1500 | medium | medium | Default balanced option |
| **gpt5-balanced-high-reasoning** | gpt-5 | 1500 | medium | high | Complex problems, standard length |
| **gpt5-detailed** | gpt-5 | 2000 | high | medium | Comprehensive explanations |
| **gpt5-verbose** | gpt-5 | 2500 | high | minimal | Long-form content, less analysis |
| **gpt5-thorough** | gpt-5 | 3000 | high | high | Maximum quality responses |
| **gpt5-extended** | gpt-5 | 4000 | high | high | Very long, detailed responses |

## Configuration Parameters

### Model
- **gpt-5-mini**: Faster, lower cost variant
- **gpt-5**: Standard GPT-5 model

### Verbosity Levels
- **low**: Concise, to-the-point responses
- **medium**: Balanced detail level
- **high**: Comprehensive, detailed explanations

### Reasoning Effort
- **minimal**: Quick responses with basic reasoning
- **medium**: Balanced thinking and analysis
- **high**: Deep reasoning and careful consideration

### Max Output Tokens
- **500-600**: Very brief responses
- **800-1000**: Short to medium responses
- **1500-2000**: Standard to detailed responses
- **2500-4000**: Long-form, comprehensive responses

## Use Case Recommendations

### Quick Tasks & Prototyping
- **gpt5-mini-fast**: Fastest and cheapest for simple tasks
- **gpt5-minimal**: Quick GPT-5 responses

### General Purpose
- **gpt5-mini-balanced**: Good balance for most tasks
- **gpt5-standard**: Default choice for quality work

### Analysis & Problem Solving
- **gpt5-compact**: Deep thinking in brief format
- **gpt5-balanced-high-reasoning**: Complex problems
- **gpt5-thorough**: Maximum analytical depth

### Content Creation
- **gpt5-concise**: Brief articles or summaries
- **gpt5-detailed**: Comprehensive articles
- **gpt5-verbose**: Long-form content
- **gpt5-extended**: Very detailed documentation

### Mixed Requirements
- **gpt5-detailed**: Balance of detail and reasoning
- **gpt5-thorough**: When quality is paramount

## Cost vs Quality Trade-offs

### Budget-Conscious
1. gpt5-mini-fast (lowest cost)
2. gpt5-mini-balanced
3. gpt5-minimal

### Balanced
1. gpt5-concise
2. gpt5-standard
3. gpt5-detailed

### Premium Quality
1. gpt5-balanced-high-reasoning
2. gpt5-thorough
3. gpt5-extended (highest cost)

## Testing Strategy

### Phase 1: Quick Testing
Start with these to understand the spectrum:
- gpt5-mini-fast (baseline)
- gpt5-standard (balanced)
- gpt5-thorough (high quality)

### Phase 2: Fine-Tuning
Based on Phase 1 results, test variations:
- If standard was good but slow → try gpt5-concise
- If thorough was overkill → try gpt5-detailed
- If mini-fast was sufficient → stick with it!

### Phase 3: Edge Cases
Test specific combinations for your use case:
- Need brief but smart? → gpt5-compact
- Need detailed but fast? → gpt5-verbose
- Need maximum everything? → gpt5-extended

## Creating Custom Configs

To create your own configuration:

```json
{
  "model": "gpt-5",
  "max_output_tokens": 1200,
  "verbosity": "medium",
  "reasoning_effort": "high"
}
```

Guidelines:
- Start with a preset and adjust
- Test token limits for your use case
- Higher reasoning = slower but more accurate
- Higher verbosity = longer responses

## Notes

- GPT-5 models do **NOT** support the `temperature` parameter
- All token limits are for output only (input not included)
- Actual output may be shorter than max_output_tokens
- Cost scales with both model choice and token usage
- Reasoning effort significantly impacts latency

## Quick Reference

**Need speed?** → gpt5-mini-fast, gpt5-minimal
**Need quality?** → gpt5-thorough, gpt5-extended
**Need balance?** → gpt5-standard, gpt5-balanced-high-reasoning
**Need brevity?** → gpt5-concise, gpt5-compact
**Need detail?** → gpt5-detailed, gpt5-verbose

Test multiple configs to find the sweet spot for your specific use case!
