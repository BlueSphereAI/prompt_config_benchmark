#!/usr/bin/env python
"""
Verification script to audit experiment parameters.

This script queries the database to show which parameters were actually used
in experiments, helping verify that different configs are truly being tested
with different parameters.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from prompt_benchmark.storage import ResultStorage


def verify_experiment_parameters(storage, hours=24, prompt_name=None):
    """
    Verify which parameters were used in recent experiments.

    Args:
        storage: ResultStorage instance
        hours: Look at experiments from last N hours (default: 24)
        prompt_name: Optional filter by prompt name
    """
    print(f"\n{'='*80}")
    print(f"EXPERIMENT PARAMETER VERIFICATION")
    print(f"{'='*80}\n")

    # Get all results
    from prompt_benchmark.storage import DBExperimentResult
    from sqlalchemy.orm import Session

    with Session(storage.engine) as session:
        query = session.query(DBExperimentResult)

        # Filter by time if specified
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(DBExperimentResult.start_time >= cutoff_time)
            print(f"Analyzing experiments from the last {hours} hours\n")

        # Filter by prompt if specified
        if prompt_name:
            query = query.filter(DBExperimentResult.prompt_name == prompt_name)
            print(f"Filtering by prompt: {prompt_name}\n")

        results = query.all()

        if not results:
            print("No experiments found matching criteria.")
            return

        print(f"Found {len(results)} experiments\n")

        # Group by prompt and config
        by_prompt = defaultdict(lambda: defaultdict(list))

        for result in results:
            config = json.loads(result.config_json)

            # Extract key parameters
            params = {
                'model': config.get('model'),
                'verbosity': config.get('verbosity'),
                'reasoning_effort': config.get('reasoning_effort'),
                'max_output_tokens': config.get('max_output_tokens'),
                'temperature': config.get('temperature'),
            }

            by_prompt[result.prompt_name][result.config_name].append({
                'experiment_id': result.experiment_id,
                'start_time': result.start_time,
                'params': params,
                'success': result.success,
                'response_length': len(result.response) if result.response else 0,
                'duration': result.duration_seconds,
            })

        # Display results
        for prompt_name, configs in by_prompt.items():
            print(f"\n{'─'*80}")
            print(f"PROMPT: {prompt_name}")
            print(f"{'─'*80}\n")

            # Check for parameter variation
            all_params = []
            for config_name, experiments in configs.items():
                if experiments:
                    all_params.append(experiments[0]['params'])

            # Detect if all configs have same parameters
            unique_verbosities = set(p['verbosity'] for p in all_params)
            unique_reasoning = set(p['reasoning_effort'] for p in all_params)

            if len(unique_verbosities) == 1 and len(unique_reasoning) == 1:
                print("⚠️  WARNING: All configs have IDENTICAL verbosity and reasoning_effort!")
                print(f"   Verbosity: {list(unique_verbosities)[0]}")
                print(f"   Reasoning: {list(unique_reasoning)[0]}\n")
            else:
                print("✓ Configs have different parameters")
                print(f"   Verbosity values: {sorted(unique_verbosities)}")
                print(f"   Reasoning values: {sorted(unique_reasoning)}\n")

            # Show each config
            for config_name, experiments in sorted(configs.items()):
                print(f"\nConfig: {config_name}")
                print(f"  Experiments: {len(experiments)}")

                if experiments:
                    params = experiments[0]['params']
                    print(f"  Parameters:")
                    print(f"    - Model: {params['model']}")
                    print(f"    - Verbosity: {params['verbosity']}")
                    print(f"    - Reasoning Effort: {params['reasoning_effort']}")
                    print(f"    - Max Tokens: {params['max_output_tokens']}")
                    print(f"    - Temperature: {params['temperature']}")

                    # Show response characteristics
                    avg_length = sum(e['response_length'] for e in experiments) / len(experiments)
                    avg_duration = sum(e['duration'] for e in experiments) / len(experiments)
                    success_rate = sum(1 for e in experiments if e['success']) / len(experiments) * 100

                    print(f"  Results:")
                    print(f"    - Avg Response Length: {avg_length:.0f} chars")
                    print(f"    - Avg Duration: {avg_duration:.2f}s")
                    print(f"    - Success Rate: {success_rate:.0f}%")

        print(f"\n{'='*80}\n")


def show_parameter_summary(storage):
    """Show summary of all unique parameter combinations."""
    print(f"\n{'='*80}")
    print(f"PARAMETER COMBINATION SUMMARY")
    print(f"{'='*80}\n")

    from prompt_benchmark.storage import DBExperimentResult
    from sqlalchemy.orm import Session

    with Session(storage.engine) as session:
        results = session.query(DBExperimentResult).all()

        if not results:
            print("No experiments found in database.")
            return

        # Collect unique parameter combinations
        param_combos = defaultdict(lambda: {'count': 0, 'configs': set()})

        for result in results:
            config = json.loads(result.config_json)

            key = (
                config.get('model'),
                config.get('verbosity'),
                config.get('reasoning_effort'),
            )

            param_combos[key]['count'] += 1
            param_combos[key]['configs'].add(result.config_name)

        print(f"Found {len(param_combos)} unique parameter combinations:\n")

        for (model, verbosity, reasoning), data in sorted(param_combos.items()):
            print(f"Model: {model}, Verbosity: {verbosity}, Reasoning: {reasoning}")
            print(f"  Used in {data['count']} experiments")
            print(f"  Configs: {', '.join(sorted(data['configs']))}")
            print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify experiment parameters in the database"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look at experiments from last N hours (default: 24, use 0 for all)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Filter by specific prompt name"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary of all unique parameter combinations"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/results/benchmark.db",
        help="Path to database file"
    )

    args = parser.parse_args()

    # Initialize storage
    db_url = f"sqlite:///{args.db}"
    storage = ResultStorage(db_url)

    if args.summary:
        show_parameter_summary(storage)
    else:
        verify_experiment_parameters(
            storage,
            hours=args.hours if args.hours > 0 else None,
            prompt_name=args.prompt
        )


if __name__ == "__main__":
    main()
