#!/usr/bin/env python3
"""
Migration script to add experiment_runs table and run_id column.

This script:
1. Creates the experiment_runs table
2. Adds run_id column to experiment_results table
3. Backfills run_id for existing experiments (each gets its own run)
4. Creates run records for all backfilled data
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from src.prompt_benchmark.storage import Base, DBExperimentResult

# Load environment variables
load_dotenv()

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")


def run_migration():
    """Run the migration to add experiment runs support."""
    print("=" * 70)
    print("EXPERIMENT RUNS MIGRATION")
    print("=" * 70)
    print()

    # Connect to database
    engine = create_engine(DATABASE_URL)

    # Step 1: Create experiment_runs table
    print("Step 1: Creating experiment_runs table...")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS experiment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                prompt_name TEXT NOT NULL,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                status TEXT NOT NULL,
                num_configs INTEGER NOT NULL,
                total_cost REAL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ experiment_runs table created")

    # Step 2: Add indexes for performance
    print("\nStep 2: Creating indexes...")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_runs_run_id
            ON experiment_runs(run_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_runs_prompt_name
            ON experiment_runs(prompt_name)
        """))
        print("✓ Indexes created")

    # Step 3: Add run_id column to experiment_results
    print("\nStep 3: Adding run_id column to experiment_results...")
    with engine.begin() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('experiment_results')
            WHERE name='run_id'
        """))
        column_exists = result.fetchone()[0] > 0

        if not column_exists:
            conn.execute(text("""
                ALTER TABLE experiment_results
                ADD COLUMN run_id TEXT
            """))
            print("✓ run_id column added")
        else:
            print("✓ run_id column already exists")

    # Step 4: Create index on run_id
    print("\nStep 4: Creating index on experiment_results.run_id...")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exp_results_run_id
            ON experiment_results(run_id)
        """))
        print("✓ Index created")

    # Step 5: Backfill data for existing experiments
    print("\nStep 5: Backfilling existing experiments...")
    with Session(engine) as session:
        # Get all experiments that don't have a run_id yet
        experiments = session.query(DBExperimentResult).filter(
            DBExperimentResult.run_id == None
        ).order_by(DBExperimentResult.prompt_name, DBExperimentResult.created_at).all()

        if not experiments:
            print("✓ No experiments to backfill")
        else:
            print(f"  Found {len(experiments)} experiments without run_id")

            # Group experiments by prompt_name
            from collections import defaultdict
            experiments_by_prompt = defaultdict(list)
            for exp in experiments:
                experiments_by_prompt[exp.prompt_name].append(exp)

            print(f"  Grouped into {len(experiments_by_prompt)} prompts")

            runs_created = 0
            experiments_updated = 0

            # Create one run per prompt with all its experiments
            for prompt_name, prompt_experiments in experiments_by_prompt.items():
                # Generate unique run_id for this prompt
                new_run_id = f"run_{uuid.uuid4().hex[:16]}"

                # Get timing from first and last experiments
                first_exp = min(prompt_experiments, key=lambda e: e.created_at)
                last_exp = max(prompt_experiments, key=lambda e: e.created_at)

                # Calculate total cost for all experiments in this run
                total_cost = sum(exp.estimated_cost_usd or 0.0 for exp in prompt_experiments)

                # Check if any experiment has AI evaluations
                has_ai_eval = False
                for exp in prompt_experiments:
                    count = session.execute(text("""
                        SELECT COUNT(*) FROM ai_evaluations
                        WHERE experiment_id = :exp_id
                    """), {"exp_id": exp.experiment_id}).scalar()
                    if count > 0:
                        has_ai_eval = True
                        break

                run_status = "analysis_completed" if has_ai_eval else "experiment_completed"

                # Create run record
                session.execute(text("""
                    INSERT INTO experiment_runs (
                        run_id, prompt_name, started_at, completed_at,
                        status, num_configs, total_cost, created_at
                    )
                    VALUES (
                        :run_id, :prompt_name, :started_at, :completed_at,
                        :status, :num_configs, :total_cost, :created_at
                    )
                """), {
                    "run_id": new_run_id,
                    "prompt_name": prompt_name,
                    "started_at": first_exp.start_time,
                    "completed_at": last_exp.end_time,
                    "status": run_status,
                    "num_configs": len(prompt_experiments),
                    "total_cost": total_cost,
                    "created_at": first_exp.created_at
                })
                runs_created += 1

                # Update all experiments with the same run_id
                for exp in prompt_experiments:
                    exp.run_id = new_run_id
                    experiments_updated += 1

                print(f"  Created run for '{prompt_name}' with {len(prompt_experiments)} experiments")

            # Final commit
            session.commit()
            print(f"✓ Created {runs_created} runs")
            print(f"✓ Updated {experiments_updated} experiments")

    # Step 6: Verify migration
    print("\nStep 6: Verifying migration...")
    with Session(engine) as session:
        total_experiments = session.query(DBExperimentResult).count()
        experiments_with_run_id = session.query(DBExperimentResult).filter(
            DBExperimentResult.run_id != None
        ).count()
        total_runs = session.execute(text("SELECT COUNT(*) FROM experiment_runs")).scalar()

        print(f"  Total experiments: {total_experiments}")
        print(f"  Experiments with run_id: {experiments_with_run_id}")
        print(f"  Total runs: {total_runs}")

        if experiments_with_run_id == total_experiments:
            print("✓ All experiments have run_id")
        else:
            missing = total_experiments - experiments_with_run_id
            print(f"⚠ Warning: {missing} experiments still missing run_id")

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - experiment_runs table created")
    print("  - run_id column added to experiment_results")
    print("  - Existing experiments backfilled with run_id")
    print("  - Each existing experiment assigned its own run")
    print()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
