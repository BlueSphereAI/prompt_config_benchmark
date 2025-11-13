#!/usr/bin/env python3
"""
Migration script to fix ExperimentRun status for runs that have completed AI evaluations.

This script updates all experiment runs that have completed AI evaluation batches
but still show status="experiment_completed" instead of "analysis_completed".

Usage:
    python scripts/fix_ai_ranking_status.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.prompt_benchmark.storage import ResultStorage, DBExperimentRun, DBAIEvaluationBatch
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table

console = Console()


def fix_ai_ranking_status():
    """Fix status for runs that have completed AI evaluations."""

    console.print("\n[bold cyan]AI Ranking Status Migration[/bold cyan]")
    console.print("=" * 60)

    # Initialize storage
    storage = ResultStorage()

    try:
        # Find all runs with experiment_completed status that have completed AI batches
        with Session(storage.engine) as session:
            # Subquery to find prompt_names with completed AI batches
            completed_batches_subq = (
                select(DBAIEvaluationBatch.prompt_name)
                .where(DBAIEvaluationBatch.status == "completed")
                .distinct()
                .subquery()
            )

            # Find runs that need updating (matching by prompt_name)
            stmt = (
                select(DBExperimentRun)
                .where(
                    and_(
                        DBExperimentRun.status == "experiment_completed",
                        DBExperimentRun.prompt_name.in_(select(completed_batches_subq))
                    )
                )
            )

            runs_to_update = session.execute(stmt).scalars().all()

        if not runs_to_update:
            console.print("\n[green]✓ No runs need updating. All statuses are correct![/green]")
            return

        # Display what will be updated
        console.print(f"\n[yellow]Found {len(runs_to_update)} run(s) with completed AI evaluations[/yellow]")

        table = Table(title="Runs to Update")
        table.add_column("Run ID", style="cyan")
        table.add_column("Prompt Name", style="magenta")
        table.add_column("Current Status", style="yellow")

        for run in runs_to_update:
            table.add_row(
                run.run_id,
                run.prompt_name,
                run.status
            )

        console.print(table)

        # Ask for confirmation
        console.print("\n[yellow]Update these runs to 'analysis_completed' status?[/yellow]")
        response = input("Enter 'yes' to proceed: ").strip().lower()

        if response != 'yes':
            console.print("[red]Migration cancelled.[/red]")
            return

        # Update each run
        updated_count = 0
        for run in runs_to_update:
            success = storage.update_run_status(
                run.run_id,
                status="analysis_completed"
            )
            if success:
                updated_count += 1
                console.print(f"[green]✓ Updated run {run.run_id} ({run.prompt_name})[/green]")
            else:
                console.print(f"[red]✗ Failed to update run {run.run_id}[/red]")

        console.print(f"\n[bold green]Migration complete! Updated {updated_count}/{len(runs_to_update)} runs.[/bold green]")

        # Show verification
        console.print("\n[cyan]Verifying updates...[/cyan]")
        with Session(storage.engine) as session:
            stmt = select(func.count()).select_from(DBExperimentRun).where(
                DBExperimentRun.status == "analysis_completed"
            )
            analysis_completed_count = session.execute(stmt).scalar()

        console.print(f"[green]Total runs with 'analysis_completed' status: {analysis_completed_count}[/green]")

    except Exception as e:
        console.print(f"\n[bold red]Error during migration: {str(e)}[/bold red]")
        raise


if __name__ == "__main__":
    fix_ai_ranking_status()
