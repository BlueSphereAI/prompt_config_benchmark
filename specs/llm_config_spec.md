# Tiered LLM Configuration Setup Guide

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Configuration Setup](#configuration-setup)
  - [1. Environment Variables](#1-environment-variables)
  - [2. GitHub Repository Variables](#2-github-repository-variables)
  - [3. Langfuse Prompt Configuration](#3-langfuse-prompt-configuration)
- [Configuration Reference](#configuration-reference)
  - [Tier Definitions](#tier-definitions)
  - [Provider-Specific Parameters](#provider-specific-parameters)
  - [Config Format Examples](#config-format-examples)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Introduction

The Tiered LLM Configuration system provides a flexible, centralized way to manage model configurations across multiple AI providers (OpenAI, Anthropic Claude, Google Gemini, and Grok). It supports:

- **Three performance tiers**: Fast, Smart, and Reasoning
- **Per-prompt overrides**: Configure specific parameters (temperature, max tokens, etc.) for individual prompts via Langfuse
- **Multiple providers**: OpenAI, Anthropic, Google Gemini, and Grok
- **Hierarchical config resolution**: Langfuse overrides → GitHub JSON configs → Legacy env vars → Hardcoded defaults
- **Backward compatibility**: Existing legacy model environment variables continue to work

This system allows you to:
1. Define default configurations for each tier and provider
2. Override configurations on a per-prompt basis through Langfuse
3. Dynamically adjust model behavior without code changes

---

## Prerequisites

Before setting up the tiered LLM configuration system, ensure you have:

1. **Access to GitHub Repository Settings**
   - Admin/write access to set repository variables
   - Repository: `BlueSphereAI/site_gen`

2. **Langfuse Instance**
   - Running Langfuse instance (dev/test/prod)
   - Admin access to create and modify prompts
   - Langfuse connection configured in application

3. **API Keys**
   - OpenAI API key (for GPT models)
   - Anthropic API key (for Claude models)
   - Google API key (for Gemini models)
   - Grok API key (for Grok models)

4. **Environment Access**
   - Access to local `.env` file for development
   - Access to deployment environments (dev/test/prod)

---

## Architecture Overview

### Configuration Hierarchy

The system resolves configurations in the following priority order (highest to lowest):

```
1. Langfuse Prompt Config (per-prompt overrides)
   ↓
2. GitHub Repository Variables (JSON tier configs)
   ↓
3. Legacy Environment Variables (backward compatibility)
   ↓
4. Hardcoded Defaults (fallback)
```

### Tier System

Three tiers are available for each provider:

| Tier | Use Case | Characteristics |
|------|----------|-----------------|
| **Fast** | Quick operations, drafts, bulk processing | Lower cost, faster response, lower quality |
| **Smart** | Default tier for most operations | Balanced cost/quality/speed |
| **Reasoning** | Complex analysis, high-quality output | Highest quality, slower, higher cost |

### Flow Diagram

```
┌─────────────────┐
│ Service Layer   │
│ (idea.py, etc.) │
└────────┬────────┘
         │
         ├─ langfuse_prompt_args={"name": "generate-idea"}
         │
         ▼
┌─────────────────────────┐
│ openai_client.py        │
│ ainvoke_json()          │
└────────┬────────────────┘
         │
         ├─ 1. Get Langfuse prompt config
         │    ├─ tier: "smart" | "fast" | "reasoning"
         │    └─ overrides: {temperature: 0.5, ...}
         │
         ├─ 2. Load base config for tier from GitHub JSON
         │    └─ OPENAI_SMART_CONFIG, CLAUDE_REASONING_CONFIG, etc.
         │
         ├─ 3. Merge configs (Langfuse overrides base)
         │
         ├─ 4. Normalize parameters for provider
         │    └─ max_output_tokens → max_tokens (Claude)
         │
         └─ 5. Call LLM with final config
```

---

## Configuration Setup

### 1. Environment Variables

#### Local Development (.env)

Add the following 12 tiered config variables to your `backend/.env` file:

```bash
# Tiered LLM Configurations (JSON format)

# OpenAI Configs
OPENAI_FAST_CONFIG={"model":"gpt-5-mini","text":{"verbosity":"low"},"reasoning":{"effort":"minimal"},"temperature":0.2,"max_output_tokens":600}
OPENAI_SMART_CONFIG={"model":"gpt-5","text":{"verbosity":"medium"},"reasoning":{"effort":"medium"},"temperature":0.35,"max_output_tokens":1500}
OPENAI_REASONING_CONFIG={"model":"gpt-5","text":{"verbosity":"medium"},"reasoning":{"effort":"high"},"temperature":0.2,"max_output_tokens":3000}

# Claude Configs
CLAUDE_FAST_CONFIG={"model":"claude-3-5-haiku-latest","max_tokens":600,"temperature":0.3}
CLAUDE_SMART_CONFIG={"model":"claude-sonnet-4-20250514","max_tokens":1500,"temperature":0.35}
CLAUDE_REASONING_CONFIG={"model":"claude-sonnet-4-20250514","max_tokens":3000,"temperature":0.2}

# Gemini Configs
GEMINI_FAST_CONFIG={"model":"gemini-2.5-flash","generation_config":{"temperature":0.2,"max_output_tokens":600}}
GEMINI_SMART_CONFIG={"model":"gemini-2.5-pro","generation_config":{"temperature":0.35,"max_output_tokens":1500}}
GEMINI_REASONING_CONFIG={"model":"gemini-2.5-pro","generation_config":{"temperature":0.2,"max_output_tokens":3000}}

# Grok Configs
GROK_FAST_CONFIG={"model":"grok-3-fast","temperature":0.3,"max_tokens":600}
GROK_SMART_CONFIG={"model":"grok-4-0709","temperature":0.35,"max_tokens":1500}
GROK_REASONING_CONFIG={"model":"grok-4-0709","temperature":0.2,"max_tokens":3000}
```

**Note**: Keep existing legacy model variables for backward compatibility:
```bash
OPENAI_SMART_MODEL=gpt-5
OPENAI_FAST_MODEL=gpt-5-mini
OPENAI_REASONING_MODEL=gpt-5
# ... etc
```

---

### 2. GitHub Repository Variables

Add the following 12 repository variables in GitHub Settings:

**Navigation**: Repository → Settings → Secrets and variables → Actions → Variables

| Variable Name | Value |
|---------------|-------|
| `OPENAI_FAST_CONFIG` | `{"model":"gpt-5-mini","text":{"verbosity":"low"},"reasoning":{"effort":"minimal"},"temperature":0.2,"max_output_tokens":600}` |
| `OPENAI_SMART_CONFIG` | `{"model":"gpt-5","text":{"verbosity":"medium"},"reasoning":{"effort":"medium"},"temperature":0.35,"max_output_tokens":1500}` |
| `OPENAI_REASONING_CONFIG` | `{"model":"gpt-5","text":{"verbosity":"medium"},"reasoning":{"effort":"high"},"temperature":0.2,"max_output_tokens":3000}` |
| `CLAUDE_FAST_CONFIG` | `{"model":"claude-3-5-haiku-latest","max_tokens":600,"temperature":0.3}` |
| `CLAUDE_SMART_CONFIG` | `{"model":"claude-sonnet-4-20250514","max_tokens":1500,"temperature":0.35}` |
| `CLAUDE_REASONING_CONFIG` | `{"model":"claude-sonnet-4-20250514","max_tokens":3000,"temperature":0.2}` |
| `GEMINI_FAST_CONFIG` | `{"model":"gemini-2.5-flash","generation_config":{"temperature":0.2,"max_output_tokens":600}}` |
| `GEMINI_SMART_CONFIG` | `{"model":"gemini-2.5-pro","generation_config":{"temperature":0.35,"max_output_tokens":1500}}` |
| `GEMINI_REASONING_CONFIG` | `{"model":"gemini-2.5-pro","generation_config":{"temperature":0.2,"max_output_tokens":3000}}` |
| `GROK_FAST_CONFIG` | `{"model":"grok-3-fast","temperature":0.3,"max_tokens":600}` |
| `GROK_SMART_CONFIG` | `{"model":"grok-4-0709","temperature":0.35,"max_tokens":1500}` |
| `GROK_REASONING_CONFIG` | `{"model":"grok-4-0709","temperature":0.2,"max_tokens":3000}` |

These variables are automatically loaded in CI/CD workflows:
- `.github/workflows/deploy.dev.yml`
- `.github/workflows/deploy.test.yml`
- `.github/workflows/test.yml`

---

### 3. Langfuse Prompt Configuration

#### Config Format

Each Langfuse prompt can include a `config` field with the following flat JSON structure:

```json
{
  "model": "fast | smart | reasoning",
  "max_output_tokens": 2400,
  "temperature": 0.2,
  "verbosity": "low | medium | high",
  "reasoning_effort": "minimal | medium | high"
}
```

#### Field Descriptions

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `model` | string | Tier selection (overrides default) | `"fast"`, `"smart"`, `"reasoning"` |
| `max_output_tokens` | integer | Maximum tokens in response | `600`, `1500`, `3000` |
| `temperature` | float | Randomness (0.0-2.0) | `0.2`, `0.35`, `0.7` |
| `verbosity` | string | GPT-5 text verbosity level | `"low"`, `"medium"`, `"high"` |
| `reasoning_effort` | string | GPT-5 reasoning effort | `"minimal"`, `"medium"`, `"high"` |

#### Example: Configuring a Prompt in Langfuse

1. Navigate to your Langfuse instance
2. Go to **Prompts** → Find your prompt (e.g., `generate-idea`)
3. Edit the prompt
4. Add/modify the `config` field:

```json
{
  "model": "reasoning",
  "max_output_tokens": 3000,
  "temperature": 0.15,
  "verbosity": "high",
  "reasoning_effort": "high"
}
```

5. Save the prompt

**Result**: The `generate-idea` prompt will now use the "reasoning" tier with custom overrides.

#### Config Resolution Example

For prompt `generate-idea` with Langfuse config:
```json
{
  "model": "smart",
  "temperature": 0.5
}
```

**Resolution Process**:
1. Tier selected: `smart` (from Langfuse)
2. Base config loaded: `OPENAI_SMART_CONFIG` from GitHub
3. Override applied: `temperature: 0.5` (from Langfuse overrides base value)
4. Final config: Base config merged with `{temperature: 0.5}`

---

## Configuration Reference

### Tier Definitions

#### Fast Tier
- **Purpose**: Quick operations, bulk processing, drafts
- **Models**:
  - OpenAI: `gpt-5-mini`
  - Claude: `claude-3-5-haiku-latest`
  - Gemini: `gemini-2.5-flash`
  - Grok: `grok-3-fast`
- **Typical Settings**:
  - Temperature: `0.2-0.3`
  - Max tokens: `600`
  - GPT-5 verbosity: `low`, reasoning: `minimal`

#### Smart Tier (Default)
- **Purpose**: Balanced quality/cost for most operations
- **Models**:
  - OpenAI: `gpt-5`
  - Claude: `claude-sonnet-4-20250514`
  - Gemini: `gemini-2.5-pro`
  - Grok: `grok-4-0709`
- **Typical Settings**:
  - Temperature: `0.35`
  - Max tokens: `1500`
  - GPT-5 verbosity: `medium`, reasoning: `medium`

#### Reasoning Tier
- **Purpose**: Complex analysis, high-quality output
- **Models**:
  - OpenAI: `gpt-5`
  - Claude: `claude-sonnet-4-20250514`
  - Gemini: `gemini-2.5-pro`
  - Grok: `grok-4-0709`
- **Typical Settings**:
  - Temperature: `0.2`
  - Max tokens: `3000`
  - GPT-5 verbosity: `medium`, reasoning: `high`

---

### Provider-Specific Parameters

#### OpenAI (GPT-5)
```json
{
  "model": "gpt-5",
  "max_output_tokens": 1500,
  "text": {
    "verbosity": "medium"
  },
  "reasoning": {
    "effort": "medium"
  }
}
```
**Note**: GPT-5 does **NOT** support `temperature` parameter.

#### Anthropic Claude
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1500,
  "temperature": 0.35
}
```
**Note**: Claude uses `max_tokens` (not `max_output_tokens`).

#### Google Gemini
```json
{
  "model": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.35,
    "max_output_tokens": 1500
  }
}
```
**Note**: Gemini wraps parameters in `generation_config`.

#### Grok
```json
{
  "model": "grok-4-0709",
  "temperature": 0.35,
  "max_tokens": 1500
}
```

---

### Config Format Examples

#### Example 1: Simple Tier Override
```json
{
  "model": "fast"
}
```
**Result**: Uses fast tier base config with no additional overrides.

#### Example 2: Tier + Temperature Override
```json
{
  "model": "smart",
  "temperature": 0.7
}
```
**Result**: Uses smart tier base config, but sets temperature to 0.7.

#### Example 3: Tier + Multiple Overrides
```json
{
  "model": "reasoning",
  "max_output_tokens": 4000,
  "temperature": 0.1,
  "verbosity": "high"
}
```
**Result**: Uses reasoning tier with custom token limit, temperature, and verbosity.

#### Example 4: GPT-5 Specific Configuration
```json
{
  "model": "reasoning",
  "max_output_tokens": 3000,
  "verbosity": "high",
  "reasoning_effort": "high"
}
```
**Note**: No `temperature` for GPT-5 models.

---

## Verification

### 1. Verify Environment Variables

**Development**:
```bash
cd backend
source .env
echo $OPENAI_SMART_CONFIG
```

**Expected Output**: JSON config string

### 2. Verify GitHub Variables

1. Go to: `https://github.com/BlueSphereAI/site_gen/settings/variables/actions`
2. Confirm all 12 `*_CONFIG` variables are present
3. Verify JSON values are valid

### 3. Verify Langfuse Connection

```bash
# Start services
make docker-up
./backend/scripts/start-backend.sh

# Check logs for Langfuse connection
tail -f /var/log/busgen/backend.log | grep -i langfuse
```

**Expected**: No connection errors

### 4. Test Config Resolution

Create a test script (`test_config.py`):

```python
import os
import json
from app.utils.langfuse_client import langfuse_client

# Test loading tier config
config = langfuse_client.get_config_overrides(name="generate-idea")
print(f"Tier: {config['tier']}")
print(f"Overrides: {json.dumps(config['overrides'], indent=2)}")

# Test environment variable parsing
openai_smart = os.getenv("OPENAI_SMART_CONFIG")
if openai_smart:
    parsed = json.loads(openai_smart)
    print(f"OpenAI Smart Config: {json.dumps(parsed, indent=2)}")
```

Run:
```bash
cd backend
python test_config.py
```

### 5. Monitor LLM Calls

Check Langfuse dashboard to verify:
- Correct models are being used
- Tier selections are working
- Overrides are applied

**Langfuse URL**: Check `LANGFUSE_HOST` in your `.env`

---

## Troubleshooting

### Issue: "Failed to get config overrides from Langfuse"

**Symptoms**: Warning logs about Langfuse config failures

**Causes**:
1. Langfuse connection not configured
2. Prompt doesn't exist in Langfuse
3. Invalid JSON in prompt config

**Solutions**:
1. Verify Langfuse credentials in `.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://langfuse.yourdomain.com
   ```
2. Create the prompt in Langfuse UI
3. Validate JSON format in Langfuse config field

---

### Issue: "Invalid JSON in tier config"

**Symptoms**: JSON parsing errors in logs

**Causes**:
1. Malformed JSON in GitHub variable
2. Invalid JSON in `.env` file

**Solutions**:
1. Validate JSON using online validator (jsonlint.com)
2. Ensure proper escaping in `.env`:
   ```bash
   # Correct
   OPENAI_SMART_CONFIG={"model":"gpt-5","temperature":0.35}

   # Incorrect (quotes not escaped)
   OPENAI_SMART_CONFIG='{"model":"gpt-5","temperature":0.35}'
   ```

---

### Issue: Wrong model being used

**Symptoms**: Unexpected model in Langfuse traces

**Causes**:
1. Tier not specified in Langfuse config
2. Wrong tier selected
3. Legacy env vars taking precedence

**Solutions**:
1. Add `"model": "smart"` to Langfuse prompt config
2. Verify tier name is correct (`fast`/`smart`/`reasoning`)
3. Check config resolution order in logs

---

### Issue: Parameters not being applied

**Symptoms**: Temperature/max_tokens different than expected

**Causes**:
1. Provider-specific parameter naming
2. Config merge order incorrect
3. Provider doesn't support parameter

**Solutions**:
1. Use provider-specific parameter names:
   - OpenAI: `max_output_tokens`
   - Claude: `max_tokens`
   - GPT-5: No `temperature` support
2. Check merge logic in `backend/app/utils/openai_client.py`
3. Verify parameter support in provider docs

---

### Issue: Langfuse prompt not loading

**Symptoms**: Default tier always used

**Causes**:
1. Missing `langfuse_prompt_args` in service call
2. Wrong prompt name

**Solutions**:
1. Verify service file has correct call:
   ```python
   await self.openai_client.ainvoke_json(
       name="generate-idea",
       langfuse_prompt_args={"name": "generate-idea"},  # Must match
       ...
   )
   ```
2. Check prompt name exists in Langfuse

---

### Issue: Docker compose not loading configs

**Symptoms**: Configs undefined in container

**Causes**:
1. Configs not added to `docker-compose.*.yml`
2. `.env` file not being loaded

**Solutions**:
1. Verify configs in environment section:
   ```yaml
   environment:
     - OPENAI_SMART_CONFIG=${OPENAI_SMART_CONFIG}
     # ... all 12 configs
   ```
2. Ensure `.env` file exists and is loaded
3. Rebuild containers:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

---

### Debug Commands

#### Check environment variables in container
```bash
docker exec -it backend env | grep CONFIG
```

#### View config resolution logs
```bash
tail -f /var/log/busgen/backend.log | grep -i "tier\|config\|override"
```

#### Test Langfuse connection
```bash
cd backend
python -c "from app.utils.langfuse_client import langfuse_client; print(langfuse_client.get_prompt(name='generate-idea'))"
```

#### Validate JSON configs
```bash
cd backend
python -c "import os, json; print(json.loads(os.getenv('OPENAI_SMART_CONFIG')))"
```

---

## Additional Resources

- **Langfuse Documentation**: [https://langfuse.com/docs](https://langfuse.com/docs)
- **OpenAI GPT-5 Docs**: OpenAI API documentation
- **Claude API Docs**: [https://docs.anthropic.com](https://docs.anthropic.com)
- **Gemini API Docs**: [https://ai.google.dev/docs](https://ai.google.dev/docs)
- **Implementation Guide**: `backend/app/utils/openai_client.py` (lines 360-450)

---

## Summary

The Tiered LLM Configuration system provides:

✅ **Three-tier performance model** (Fast/Smart/Reasoning)
✅ **Multi-provider support** (OpenAI, Claude, Gemini, Grok)
✅ **Per-prompt customization** via Langfuse
✅ **Centralized configuration** via GitHub variables
✅ **Backward compatibility** with legacy env vars
✅ **Dynamic overrides** without code deployment

Configuration priority: **Langfuse > GitHub JSON > Legacy Env > Defaults**

For implementation details, see the codebase documentation in:
- `backend/app/utils/openai_client.py`
- `backend/app/utils/langfuse_client.py`