#!/usr/bin/env python3
"""Create all permutations of model x reasoning x verbosity configs."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_benchmark.storage import ResultStorage
import os


def create_config_permutations():
    """Delete existing configs and create all permutations."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Models to create configs for
    models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]

    # Reasoning efforts
    reasoning_efforts = ["high", "medium", "minimal"]

    # Verbosity levels
    verbosities = ["high", "medium", "low"]

    # Token limits by model
    token_limits = {
        "gpt-5": 8000,
        "gpt-5-mini": 3000,
        "gpt-5-nano": 2000
    }

    print("🗑️  Deleting all existing configs...")

    # Get all configs and delete them
    all_configs = storage.get_all_configs(active_only=False)
    for config_obj in all_configs:
        # Get the config name from database
        from prompt_benchmark.storage import DBLLMConfig
        from sqlalchemy.orm import Session as SQLSession
        from sqlalchemy import select

        with SQLSession(storage.engine) as session:
            stmt = select(DBLLMConfig).where(
                DBLLMConfig.model == config_obj.model,
                DBLLMConfig.max_output_tokens == config_obj.max_output_tokens,
                DBLLMConfig.verbosity == config_obj.verbosity,
                DBLLMConfig.reasoning_effort == config_obj.reasoning_effort
            )
            db_config = session.execute(stmt).first()
            if db_config:
                config_name = db_config[0].name
                storage.delete_config(config_name)
                print(f"  ❌ Deleted: {config_name}")

    print(f"\n✨ Creating all permutations...")
    print(f"   Models: {len(models)}")
    print(f"   Reasoning efforts: {len(reasoning_efforts)}")
    print(f"   Verbosity levels: {len(verbosities)}")
    print(f"   Total configs to create: {len(models) * len(reasoning_efforts) * len(verbosities)}\n")

    created = 0

    # Create all permutations
    for model in models:
        for reasoning in reasoning_efforts:
            for verbosity in verbosities:
                # Create config name
                model_short = model.replace("gpt-", "gpt")
                name = f"{model_short}-standard-{reasoning}-{verbosity}"

                # Get token limit for this model
                max_tokens = token_limits[model]

                # Create LangfuseConfig
                from prompt_benchmark.models import LangfuseConfig

                config = LangfuseConfig(
                    model=model,
                    max_output_tokens=max_tokens,
                    reasoning_effort=reasoning,
                    verbosity=verbosity
                )

                # Save to database
                description = f"{model} with {reasoning} reasoning and {verbosity} verbosity"
                storage.save_config(config, name, description)

                print(f"✓ Created: {name}")
                print(f"  Model: {model}, Reasoning: {reasoning}, Verbosity: {verbosity}, Max Tokens: {max_tokens}")

                created += 1

    print(f"\n✅ Successfully created {created} configs!")

    # List all configs
    all_configs = storage.get_all_configs(active_only=True)
    print(f"\nTotal configs in database: {len(all_configs)}")


if __name__ == "__main__":
    create_config_permutations()
