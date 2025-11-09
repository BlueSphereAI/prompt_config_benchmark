#!/usr/bin/env python3
"""Migrate prompts from JSON files to database."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_benchmark.storage import ResultStorage
from prompt_benchmark.models import Prompt
from prompt_benchmark.config_loader import PromptLoader
import os


def migrate_prompts():
    """Migrate prompts from data/prompts/*.json to database."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Load prompts from JSON files
    prompts_dir = Path("data/prompts")
    if not prompts_dir.exists():
        print(f"❌ Prompts directory not found: {prompts_dir}")
        return

    # Load each prompt individually to handle errors gracefully
    prompts = []
    for json_file in prompts_dir.glob("*.json"):
        try:
            prompt = PromptLoader.load_prompt_from_file(json_file)
            prompts.append(prompt)
        except Exception as e:
            print(f"⚠ Skipped {json_file.name} (invalid JSON): {e}")
            continue

    print(f"Found {len(prompts)} valid prompts in {prompts_dir}/")

    # Save each prompt to database
    migrated = 0
    skipped = 0
    errors = 0

    for prompt in prompts:
        try:
            # Check if already exists
            existing = storage.get_prompt(prompt.name)
            if existing:
                print(f"⚠ Skipped (already exists): {prompt.name}")
                skipped += 1
                continue

            # Save to database
            storage.save_prompt(prompt)
            print(f"✓ Migrated: {prompt.name}")
            migrated += 1

        except Exception as e:
            print(f"❌ Error migrating {prompt.name}: {e}")
            errors += 1

    print(f"\n✅ Migration complete!")
    print(f"   Migrated: {migrated}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors: {errors}")

    # List all prompts in database
    all_prompts = storage.get_all_prompts(active_only=False)
    print(f"\nTotal prompts in database: {len(all_prompts)}")
    for p in all_prompts:
        print(f"  • {p.name}")
        if p.description:
            print(f"    {p.description}")


if __name__ == "__main__":
    migrate_prompts()
