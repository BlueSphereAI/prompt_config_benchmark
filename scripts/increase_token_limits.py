#!/usr/bin/env python3
"""Increase token limits for configs that have experiments failing due to length."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_benchmark.storage import ResultStorage
import os


def increase_token_limits():
    """Increase token limits for configs with length failures."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Token limit increases
    updates = {
        # gpt5: -> 10000
        "gpt5-standard": 10000,
        # gpt5-mini: -> 8000
        "gpt5-mini": 8000,
        # gpt5-nano: -> 10000
        "gpt5-nano": 10000,
    }

    print("🔧 Updating token limits for configs with length failures...\n")

    # Query database directly to get config names
    from prompt_benchmark.storage import DBLLMConfig
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import select

    updated = 0
    with SQLSession(storage.engine) as session:
        stmt = select(DBLLMConfig).where(DBLLMConfig.is_active == True)
        db_configs = session.execute(stmt).scalars().all()

        for db_config in db_configs:
            # Check if config name matches any of our patterns
            for prefix, new_limit in updates.items():
                if db_config.name.startswith(prefix):
                    old_limit = db_config.max_output_tokens

                    # Get the existing config as LangfuseConfig, update, and save
                    config = storage._db_config_to_langfuse(db_config)
                    config.max_output_tokens = new_limit

                    storage.save_config(
                        config,
                        db_config.name,
                        db_config.description
                    )

                    print(f"✓ Updated {db_config.name}:")
                    print(f"  {old_limit:,} -> {new_limit:,} tokens")
                    updated += 1
                    break

    print(f"\n✅ Successfully updated {updated} configs!")

    # Show summary
    print("\n📊 Summary of updates:")
    print(f"  • gpt5-standard-* configs: -> 10,000 tokens")
    print(f"  • gpt5-mini-* configs: -> 8,000 tokens")
    print(f"  • gpt5-nano-* configs: -> 10,000 tokens")


if __name__ == "__main__":
    increase_token_limits()
