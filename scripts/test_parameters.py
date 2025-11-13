#!/usr/bin/env python
"""
Test script to verify GPT-5 parameters are being sent correctly.

This creates a minimal test without making actual API calls.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from prompt_benchmark.models import LangfuseConfig
from prompt_benchmark.executor import ExperimentExecutor


def test_parameter_preparation():
    """Test that _prepare_api_params correctly handles GPT-5 parameters."""

    print("\n" + "="*80)
    print("TESTING GPT-5 PARAMETER PREPARATION")
    print("="*80 + "\n")

    # Create executor (with fake API key for testing)
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    executor = ExperimentExecutor()

    # Test cases
    test_configs = [
        {
            "name": "gpt5-low-minimal",
            "config": LangfuseConfig(
                model="gpt-5",
                verbosity="low",
                reasoning_effort="minimal",
                max_output_tokens=8000
            )
        },
        {
            "name": "gpt5-medium-medium",
            "config": LangfuseConfig(
                model="gpt-5",
                verbosity="medium",
                reasoning_effort="medium",
                max_output_tokens=8000
            )
        },
        {
            "name": "gpt5-high-high",
            "config": LangfuseConfig(
                model="gpt-5",
                verbosity="high",
                reasoning_effort="high",
                max_output_tokens=10000
            )
        },
        {
            "name": "gpt5-mini-low-minimal",
            "config": LangfuseConfig(
                model="gpt-5-mini",
                verbosity="low",
                reasoning_effort="minimal",
                max_output_tokens=2000
            )
        },
        {
            "name": "gpt4-baseline",
            "config": LangfuseConfig(
                model="gpt-4",
                temperature=0.7,
                max_output_tokens=4000
            )
        }
    ]

    # Test messages
    messages = [{"role": "user", "content": "Test prompt"}]

    # Test each config
    for test in test_configs:
        print(f"\nConfig: {test['name']}")
        print("-" * 40)

        params = executor._prepare_api_params(test['config'], messages)

        print(f"Model: {params['model']}")

        if 'max_completion_tokens' in params:
            print(f"max_completion_tokens: {params['max_completion_tokens']}")
        elif 'max_tokens' in params:
            print(f"max_tokens: {params['max_tokens']}")

        if 'temperature' in params:
            print(f"temperature: {params['temperature']}")

        if 'verbosity' in params:
            print(f"verbosity: {params['verbosity']}")
        else:
            print("verbosity: NOT SET")

        if 'reasoning_effort' in params:
            print(f"reasoning_effort: {params['reasoning_effort']}")
        else:
            print("reasoning_effort: NOT SET")

        # Verify GPT-5 specific handling
        if test['config'].model.startswith('gpt-5'):
            # Should have max_completion_tokens, not max_tokens
            assert 'max_completion_tokens' in params, \
                f"GPT-5 should use max_completion_tokens, not max_tokens"
            assert 'max_tokens' not in params, \
                f"GPT-5 should NOT have max_tokens parameter"

            # Should have verbosity if set
            if test['config'].verbosity:
                assert 'verbosity' in params, \
                    f"GPT-5 with verbosity should have 'verbosity' parameter"
                assert params['verbosity'] == test['config'].verbosity, \
                    f"Verbosity mismatch: {params['verbosity']} != {test['config'].verbosity}"
                print("✓ Verbosity correctly set")

            # Should have reasoning effort if set
            if test['config'].reasoning_effort:
                assert 'reasoning_effort' in params, \
                    f"GPT-5 with reasoning_effort should have 'reasoning_effort' parameter"
                assert params['reasoning_effort'] == test['config'].reasoning_effort, \
                    f"Reasoning effort mismatch: {params['reasoning_effort']} != {test['config'].reasoning_effort}"
                print("✓ Reasoning effort correctly set")

            # Should NOT have temperature
            if 'temperature' in params:
                print("⚠️  WARNING: GPT-5 has temperature parameter (should be excluded)")

        else:
            # Non-GPT-5 models should use max_tokens
            if test['config'].max_output_tokens:
                assert 'max_tokens' in params, \
                    f"Non-GPT-5 should use max_tokens"
                print("✓ max_tokens correctly set for non-GPT-5 model")

    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_parameter_preparation()
