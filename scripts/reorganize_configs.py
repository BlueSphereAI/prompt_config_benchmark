#!/usr/bin/env python3
"""
Reorganize LLM configurations:
1. Delete all experiment and AI analysis data
2. Remove all existing configs
3. Create all 24 permutations (2 models × 4 reasoning × 3 verbosity)
4. Set max_output_tokens=10000 for all configs
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from prompt_benchmark.storage import ResultStorage, DBLLMConfig

def delete_experiment_and_analysis_data(session):
    """Delete all experiment and AI analysis data in correct order."""
    print("\n=== Phase 1: Deleting Experiment and AI Analysis Data ===")

    # Delete in order to handle foreign key constraints
    tables = [
        'ai_evaluations',
        'ai_evaluation_batches',
        'human_rankings',
        'evaluations',
        'experiment_results',
        'experiment_runs'
    ]

    for table in tables:
        result = session.execute(text(f"DELETE FROM {table}"))
        count = result.rowcount
        session.commit()
        print(f"  Deleted {count} records from {table}")

    print("  ✓ All experiment and AI analysis data deleted")

def delete_all_configs(session):
    """Delete all existing LLM configurations."""
    print("\n=== Phase 2: Deleting All Existing Configurations ===")

    result = session.execute(text("DELETE FROM llm_configs"))
    count = result.rowcount
    session.commit()
    print(f"  Deleted {count} existing configurations")
    print("  ✓ All configs deleted")

def create_all_permutations(session):
    """Create all 24 config permutations."""
    print("\n=== Phase 3: Creating All 24 Config Permutations ===")

    models = [
        ("gpt5", "gpt-5"),
        ("gpt5-mini", "gpt-5-mini")
    ]
    reasoning_efforts = ["high", "medium", "low", "minimal"]
    verbosities = ["high", "medium", "low"]
    max_output_tokens = 10000

    configs_created = []

    for model_short, model_full in models:
        for reasoning in reasoning_efforts:
            for verbosity in verbosities:
                name = f"{model_short}-{reasoning}-{verbosity}"

                # Create description
                description = (
                    f"{model_full.upper()} with {reasoning} reasoning effort "
                    f"and {verbosity} verbosity"
                )

                # Create config
                config = DBLLMConfig(
                    name=name,
                    model=model_full,
                    max_output_tokens=max_output_tokens,
                    verbosity=verbosity,
                    reasoning_effort=reasoning,
                    description=description,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    is_active=True
                )

                session.add(config)
                configs_created.append(name)

    session.commit()

    print(f"  Created {len(configs_created)} configurations:")
    for i, name in enumerate(configs_created, 1):
        print(f"    {i:2d}. {name}")

    print("  ✓ All 24 configs created")

def verify_final_state(session):
    """Verify the final database state."""
    print("\n=== Phase 4: Verifying Final State ===")

    # Count active configs
    result = session.execute(text("SELECT COUNT(*) FROM llm_configs WHERE is_active = 1"))
    active_count = result.scalar()

    # Count total configs
    result = session.execute(text("SELECT COUNT(*) FROM llm_configs"))
    total_count = result.scalar()

    # Get all config names
    result = session.execute(text("SELECT name FROM llm_configs ORDER BY name"))
    all_names = [row[0] for row in result.fetchall()]

    # Verify experiment data is gone
    result = session.execute(text("SELECT COUNT(*) FROM experiment_results"))
    exp_count = result.scalar()

    result = session.execute(text("SELECT COUNT(*) FROM ai_evaluations"))
    eval_count = result.scalar()

    print(f"  Total configs: {total_count}")
    print(f"  Active configs: {active_count}")
    print(f"  Experiment results: {exp_count}")
    print(f"  AI evaluations: {eval_count}")

    if total_count == 24 and active_count == 24 and exp_count == 0 and eval_count == 0:
        print("\n  ✓ SUCCESS! Database is in correct state")
        print("\n  All configurations:")
        for i, name in enumerate(all_names, 1):
            print(f"    {i:2d}. {name}")
        return True
    else:
        print("\n  ✗ ERROR! Database is not in expected state")
        if total_count != 24:
            print(f"    Expected 24 total configs, got {total_count}")
        if active_count != 24:
            print(f"    Expected 24 active configs, got {active_count}")
        if exp_count != 0:
            print(f"    Expected 0 experiment results, got {exp_count}")
        if eval_count != 0:
            print(f"    Expected 0 AI evaluations, got {eval_count}")
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("LLM Configuration Reorganization Script")
    print("=" * 60)

    # Initialize storage
    storage = ResultStorage()

    # Create a session
    session = Session(storage.engine)

    try:
        # Phase 1: Delete experiment and analysis data
        delete_experiment_and_analysis_data(session)

        # Phase 2: Delete all existing configs
        delete_all_configs(session)

        # Phase 3: Create all 24 permutations
        create_all_permutations(session)

        # Phase 4: Verify final state
        success = verify_final_state(session)

        print("\n" + "=" * 60)
        if success:
            print("REORGANIZATION COMPLETE!")
        else:
            print("REORGANIZATION FAILED - Please check errors above")
        print("=" * 60)

        return 0 if success else 1

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 1
    finally:
        session.close()

if __name__ == "__main__":
    sys.exit(main())
