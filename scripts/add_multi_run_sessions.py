#!/usr/bin/env python3
"""
Database migration script to add multi_run_sessions table and update experiment_runs.

This migration:
1. Creates multi_run_sessions table
2. Adds session_id and run_number columns to experiment_runs
3. Creates necessary indexes
4. Backfills existing runs with run_number = 1
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from prompt_benchmark.storage import ResultStorage

def run_migration():
    """Execute the migration."""
    storage = ResultStorage()
    engine = storage.engine

    with engine.connect() as conn:
        print("Starting migration: add_multi_run_sessions")

        # 1. Create multi_run_sessions table
        print("Creating multi_run_sessions table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS multi_run_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                prompt_name TEXT NOT NULL,
                num_runs INTEGER NOT NULL,
                runs_completed INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                review_prompt_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP
            )
        """))

        # 2. Create indexes on multi_run_sessions
        print("Creating indexes on multi_run_sessions...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_multi_run_sessions_session_id
            ON multi_run_sessions(session_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_multi_run_sessions_prompt_name
            ON multi_run_sessions(prompt_name)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_multi_run_sessions_status
            ON multi_run_sessions(status)
        """))

        # 3. Check if columns already exist in experiment_runs
        cursor = conn.execute(text("PRAGMA table_info(experiment_runs)"))
        columns = {row[1] for row in cursor.fetchall()}

        # 4. Add session_id column to experiment_runs if it doesn't exist
        if 'session_id' not in columns:
            print("Adding session_id column to experiment_runs...")
            conn.execute(text("""
                ALTER TABLE experiment_runs
                ADD COLUMN session_id TEXT
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_experiment_runs_session_id
                ON experiment_runs(session_id)
            """))
        else:
            print("session_id column already exists in experiment_runs")

        # 5. Add run_number column to experiment_runs if it doesn't exist
        if 'run_number' not in columns:
            print("Adding run_number column to experiment_runs...")
            conn.execute(text("""
                ALTER TABLE experiment_runs
                ADD COLUMN run_number INTEGER DEFAULT 1
            """))

            # Backfill existing runs with run_number = 1
            print("Backfilling existing runs with run_number = 1...")
            conn.execute(text("""
                UPDATE experiment_runs
                SET run_number = 1
                WHERE run_number IS NULL
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_experiment_runs_run_number
                ON experiment_runs(run_number)
            """))
        else:
            print("run_number column already exists in experiment_runs")

        conn.commit()
        print("Migration completed successfully!")

        # Print summary
        cursor = conn.execute(text("SELECT COUNT(*) FROM experiment_runs"))
        run_count = cursor.fetchone()[0]
        print(f"\nSummary:")
        print(f"  - multi_run_sessions table created")
        print(f"  - experiment_runs updated with session_id and run_number columns")
        print(f"  - {run_count} existing runs backfilled with run_number = 1")
        print(f"  - All indexes created")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
