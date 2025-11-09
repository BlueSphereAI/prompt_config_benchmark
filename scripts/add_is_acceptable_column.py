#!/usr/bin/env python3
"""
Migration script to add is_acceptable column to experiment_results table.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import prompt_benchmark
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from prompt_benchmark.storage import ResultStorage


def add_is_acceptable_column():
    """Add is_acceptable column to experiment_results table."""

    # Initialize storage
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    print("🔧 Adding is_acceptable column to experiment_results table...\n")

    # Add the column with default value True
    with storage.engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(experiment_results)"))
            columns = [row[1] for row in result]

            if 'is_acceptable' in columns:
                print("✓ Column is_acceptable already exists!")
                return

            # Add the column
            conn.execute(text(
                "ALTER TABLE experiment_results ADD COLUMN is_acceptable BOOLEAN NOT NULL DEFAULT 1"
            ))
            conn.commit()

            print("✅ Successfully added is_acceptable column!")
            print("   - Default value: TRUE (all existing experiments marked as acceptable)")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    add_is_acceptable_column()
