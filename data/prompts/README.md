# Prompt Format Guide

Prompts in this framework use the **OpenAI messages format** - an array of message objects that can include system instructions, user input, and assistant responses.

## Format

Each prompt is a JSON file containing an array of message objects:

```json
[
    {
        "role": "system",
        "content": "You are a helpful assistant..."
    },
    {
        "role": "user",
        "content": "User's question or instruction here..."
    }
]
```

## Message Roles

- **system**: Sets the behavior and context for the assistant
- **user**: User's input or question
- **assistant**: Previous assistant responses (for multi-turn conversations)

## File Naming

The filename (without `.json` extension) becomes the prompt name:
- `business-idea-cleanup.json` → name: `business-idea-cleanup`
- `code-review.json` → name: `code-review`

## Basic Example

**simple-summary.json:**
```json
[
    {
        "role": "system",
        "content": "You are a helpful assistant that creates concise summaries."
    },
    {
        "role": "user",
        "content": "Please summarize the following text in 2-3 sentences:\n\nArtificial intelligence has made remarkable progress..."
    }
]
```

## Extended Format

You can optionally include metadata by wrapping the messages in an object:

```json
{
    "name": "custom-name",
    "messages": [
        {
            "role": "system",
            "content": "System instructions..."
        },
        {
            "role": "user",
            "content": "User input..."
        }
    ],
    "description": "What this prompt does",
    "category": "text-processing",
    "tags": ["summarization", "text"]
}
```

## Multi-Turn Conversations

Include multiple exchanges:

```json
[
    {
        "role": "system",
        "content": "You are a coding tutor."
    },
    {
        "role": "user",
        "content": "How do I reverse a list in Python?"
    },
    {
        "role": "assistant",
        "content": "You can use list.reverse() or reversed()."
    },
    {
        "role": "user",
        "content": "What's the difference between them?"
    }
]
```

## System Message Best Practices

The system message sets the context and behavior:

### Good System Messages

✅ **Specific and actionable:**
```json
{
    "role": "system",
    "content": "You are an expert software entrepreneur/investor. Analyze business ideas for quick monetization potential. Focus on low-cost, fast-to-deploy solutions."
}
```

✅ **Includes constraints:**
```json
{
    "role": "system",
    "content": "You are a technical writer. Explain concepts clearly using:\n- Simple language\n- Real-world examples\n- No jargon\n- Maximum 150 words"
}
```

### Avoid

❌ **Too vague:**
```json
{
    "role": "system",
    "content": "You are helpful."
}
```

❌ **Conflicting instructions:**
```json
{
    "role": "system",
    "content": "Be concise. Provide extensive detail."
}
```

## User Message Best Practices

The user message contains the actual task:

### Good User Messages

✅ **Clear and specific:**
```json
{
    "role": "user",
    "content": "Analyze this business idea and identify:\n1. Target customers\n2. Core problem solved\n3. Revenue model\n\n[business idea here]"
}
```

✅ **Includes examples:**
```json
{
    "role": "user",
    "content": "Rewrite this description to be more concise.\n\nBad example: 'This amazing software helps you'\nGood example: 'Software that automates'\n\nDescription to rewrite:\n[text here]"
}
```

### Avoid

❌ **Ambiguous:**
```json
{
    "role": "user",
    "content": "Do something with this text"
}
```

❌ **Missing context:**
```json
{
    "role": "user",
    "content": "Fix it"
}
```

## Testing Different Prompts

To compare prompt variations:

1. Create multiple versions:
   - `idea-cleanup-v1.json`
   - `idea-cleanup-v2.json`
   - `idea-cleanup-concise.json`

2. Run experiments:
   ```bash
   benchmark run --prompt idea-cleanup-v1 --prompt idea-cleanup-v2
   ```

3. Analyze which performs better:
   ```bash
   benchmark analyze
   ```

## Tips for Prompt Engineering

1. **Be specific**: Vague instructions produce inconsistent results
2. **Show examples**: Include good/bad examples in your prompt
3. **Set constraints**: Word limits, format requirements, style guidelines
4. **Test iteratively**: Run small tests, refine, repeat
5. **Use system for role**: Put personality/expertise in system message
6. **Use user for task**: Put specific instructions in user message

## Example: Production Prompt

Here's a well-structured production prompt:

**business-analysis.json:**
```json
[
    {
        "role": "system",
        "content": "# Role\nYou are an expert software entrepreneur/investor.\n\n# Guidelines\n- Focus on facts, not fluff\n- Prioritize quick monetization\n- Emphasize practical solutions\n- Maximum 200 words per section\n\n# Output Format\nStructure your response using:\n- **Bold** for key terms\n- Bullet points for lists\n- Clear section headers"
    },
    {
        "role": "user",
        "content": "Analyze this business idea:\n\n### Idea\n[user's messy business idea]\n\n### Required Sections\n- Customer\n- Problem\n- Solution\n- Revenue Model\n- Differentiation"
    }
]
```

## Common Patterns

### Pattern: Structured Output

Force structured responses:

```json
{
    "role": "system",
    "content": "Output your response as JSON with these exact keys: 'summary', 'key_points', 'recommendation'"
}
```

### Pattern: Length Control

Control response length:

```json
{
    "role": "system",
    "content": "Rules:\n- Maximum 100 words total\n- Each bullet ≤ 15 words\n- No introductory phrases"
}
```

### Pattern: Style Enforcement

Enforce writing style:

```json
{
    "role": "system",
    "content": "Write in:\n- Active voice only\n- Present tense\n- Second person ('you')\n- No marketing jargon"
}
```

## Troubleshooting

### Issue: Inconsistent outputs

**Solution**: Add more specific constraints in system message

### Issue: Too verbose

**Solution**: Add word/bullet limits explicitly

### Issue: Wrong format

**Solution**: Show an example of correct format in the prompt

### Issue: Ignores instructions

**Solution**: Move critical instructions to user message and emphasize them

## Next Steps

1. Start with `business-idea-cleanup.json` as a template
2. Modify the system and user messages for your use case
3. Test with different configs to find optimal settings
4. Iterate based on evaluation results

For more examples, see the existing prompt files in this directory.
