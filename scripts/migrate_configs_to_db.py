#!/usr/bin/env python3
"""Migrate LLM configs from JSON files to database."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_benchmark.storage import ResultStorage
from prompt_benchmark.models import LangfuseConfig
from prompt_benchmark.config_loader import ConfigLoader
import os


def migrate_configs():
    """Migrate configs from data/configs/*.json to database."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Load configs from JSON files
    configs_dir = Path("data/configs")
    if not configs_dir.exists():
        print(f"❌ Configs directory not found: {configs_dir}")
        return

    # Load all configs
    configs = ConfigLoader.load_configs_from_directory(configs_dir)
    print(f"Found {len(configs)} configs in {configs_dir}/")

    # Save each config to database
    migrated = 0
    skipped = 0
    errors = 0

    for config_name, config in configs.items():
        try:
            # Check if already exists
            existing = storage.get_config(config_name)
            if existing:
                print(f"⚠ Skipped (already exists): {config_name}")
                skipped += 1
                continue

            # Extract description from config file path
            config_file = configs_dir / f"{config_name}.json"
            description = None
            if config_file.exists():
                with open(config_file) as f:
                    data = json.load(f)
                    description = data.get("description")

            # Save to database
            storage.save_config(config, config_name, description)
            print(f"✓ Migrated: {config_name}")
            print(f"  Model: {config.model}")
            if config.max_output_tokens:
                print(f"  Max tokens: {config.max_output_tokens}")
            if config.verbosity:
                print(f"  Verbosity: {config.verbosity}")
            if config.reasoning_effort:
                print(f"  Reasoning effort: {config.reasoning_effort}")
            migrated += 1

        except Exception as e:
            print(f"❌ Error migrating {config_name}: {e}")
            errors += 1

    print(f"\n✅ Migration complete!")
    print(f"   Migrated: {migrated}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors: {errors}")

    # List all configs in database
    all_configs = storage.get_all_configs(active_only=False)
    print(f"\nTotal configs in database: {len(all_configs)}")
    for config in all_configs:
        from prompt_benchmark.storage import DBLLMConfig
        from sqlalchemy.orm import Session as SQLSession
        from sqlalchemy import select

        # Get the name from database
        with SQLSession(storage.engine) as session:
            stmt = select(DBLLMConfig).where(
                DBLLMConfig.model == config.model,
                DBLLMConfig.max_output_tokens == config.max_output_tokens,
                DBLLMConfig.verbosity == config.verbosity,
                DBLLMConfig.reasoning_effort == config.reasoning_effort
            )
            db_config = session.execute(stmt).first()
            if db_config:
                db_config = db_config[0]
                print(f"  • {db_config.name} ({db_config.model})")
                if db_config.description:
                    print(f"    {db_config.description}")


if __name__ == "__main__":
    migrate_configs()
