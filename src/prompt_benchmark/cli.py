"""
Command-line interface for the benchmark framework.

Provides commands for running benchmarks, evaluating results, and analyzing data.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .analyzer import BenchmarkAnalyzer
from .config_loader import (
    ConfigLoader,
    PromptLoader,
    create_default_configs,
    create_example_prompts,
)
from .evaluator import AIEvaluator, HumanEvaluator
from .executor import ExperimentExecutor
from .storage import ResultStorage


# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Prompt Configuration Benchmark Framework

    A tool for testing and comparing different LLM configurations.
    """
    pass


@main.command()
@click.option(
    "--prompts-dir",
    type=click.Path(exists=True),
    default="data/prompts",
    help="Directory containing prompt definitions"
)
@click.option(
    "--configs-dir",
    type=click.Path(exists=True),
    default="data/configs",
    help="Directory containing config files"
)
@click.option(
    "--db",
    default=None,
    help="Database URL (default: from env or sqlite:///data/results/benchmark.db)"
)
@click.option(
    "--prompt",
    multiple=True,
    help="Specific prompt(s) to run (default: all)"
)
@click.option(
    "--config",
    multiple=True,
    help="Specific config(s) to use (default: all)"
)
def run(prompts_dir, configs_dir, db, prompt, config):
    """
    Run benchmark experiments.

    Execute prompts with various configurations and store results.
    """
    console.print("[bold cyan]Starting Benchmark Run[/bold cyan]\n")

    # Initialize storage
    db_url = db or os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Initialize executor
    try:
        executor = ExperimentExecutor()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)

    # Load prompts
    prompts_path = Path(prompts_dir)
    if prompts_path.exists():
        prompts = PromptLoader.load_prompts_from_directory(prompts_path)
        console.print(f"Loaded {len(prompts)} prompts from {prompts_dir}")
    else:
        console.print(f"[yellow]Prompts directory not found: {prompts_dir}[/yellow]")
        console.print("Using example prompts")
        prompts = create_example_prompts()

    # Load configs
    configs_path = Path(configs_dir)
    if configs_path.exists():
        configs = ConfigLoader.load_configs_from_directory(configs_path)
        console.print(f"Loaded {len(configs)} configs from {configs_dir}")
    else:
        console.print(f"[yellow]Configs directory not found: {configs_dir}[/yellow]")
        console.print("Using default configs")
        configs = create_default_configs()

    # Filter prompts if specified
    if prompt:
        prompts = {k: v for k, v in prompts.items() if k in prompt}
        if not prompts:
            console.print(f"[red]No prompts found matching: {prompt}[/red]")
            sys.exit(1)

    # Filter configs if specified
    if config:
        configs = {k: v for k, v in configs.items() if k in config}
        if not configs:
            console.print(f"[red]No configs found matching: {config}[/red]")
            sys.exit(1)

    # Calculate total experiments
    total = len(prompts) * len(configs)
    console.print(f"\n[bold]Running {total} experiments[/bold]")
    console.print(f"Prompts: {', '.join(prompts.keys())}")
    console.print(f"Configs: {', '.join(configs.keys())}\n")

    # Run experiments with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running experiments...", total=total)

        for prompt_name, prompt_obj in prompts.items():
            for config_name, config_obj in configs.items():
                progress.update(
                    task,
                    description=f"Running: {prompt_name} with {config_name}"
                )

                result = executor.run_experiment(
                    prompt=prompt_obj,
                    config=config_obj,
                    config_name=config_name
                )

                # Save result
                storage.save_result(result)

                if result.success:
                    progress.console.print(
                        f"  [green]✓[/green] {prompt_name} + {config_name}: "
                        f"{result.duration_seconds:.2f}s"
                    )
                else:
                    progress.console.print(
                        f"  [red]✗[/red] {prompt_name} + {config_name}: {result.error}"
                    )

                progress.advance(task)

    console.print("\n[bold green]Benchmark run complete![/bold green]")
    console.print(f"Results saved to: {db_url}")


@main.command()
@click.option(
    "--db",
    default=None,
    help="Database URL"
)
@click.option(
    "--prompt",
    help="Evaluate results for specific prompt only"
)
@click.option(
    "--evaluator",
    default=None,
    help="Your name (for tracking evaluations)"
)
@click.option(
    "--criteria",
    multiple=True,
    help="Criteria to evaluate (can specify multiple)"
)
def evaluate(db, prompt, evaluator, criteria):
    """
    Evaluate experiment results (human evaluation).

    Interactively score and provide feedback on experiment results.
    """
    console.print("[bold cyan]Human Evaluation Mode[/bold cyan]\n")

    # Initialize storage
    db_url = db or os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Initialize evaluator
    human_eval = HumanEvaluator(storage)

    # Get results to evaluate
    if prompt:
        results = storage.get_results_by_prompt(prompt)
        console.print(f"Loaded {len(results)} results for prompt '{prompt}'")
    else:
        results = storage.get_all_results()
        console.print(f"Loaded {len(results)} total results")

    # Filter out already evaluated results
    unevaluated = []
    for result in results:
        evals = storage.get_evaluations_by_experiment(result.experiment_id)
        if not evals:
            unevaluated.append(result)

    console.print(f"Found {len(unevaluated)} unevaluated results\n")

    if not unevaluated:
        console.print("[yellow]No results to evaluate![/yellow]")
        return

    # Convert criteria tuple to list
    criteria_list = list(criteria) if criteria else None

    # Run evaluation
    human_eval.evaluate_batch(
        results=unevaluated,
        evaluator_name=evaluator,
        criteria=criteria_list
    )

    console.print("\n[bold green]Evaluation complete![/bold green]")


@main.command()
@click.option(
    "--db",
    default=None,
    help="Database URL"
)
@click.option(
    "--prompt",
    help="Evaluate results for specific prompt only"
)
@click.option(
    "--model",
    default=None,
    help="Model to use as judge (default: from env or gpt-4)"
)
@click.option(
    "--criteria",
    multiple=True,
    help="Criteria to evaluate"
)
def ai_evaluate(db, prompt, model, criteria):
    """
    Evaluate experiment results using AI.

    Use an LLM to automatically score and provide feedback.
    """
    console.print("[bold cyan]AI Evaluation Mode[/bold cyan]\n")

    # Initialize storage
    db_url = db or os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)

    # Initialize AI evaluator
    try:
        ai_eval = AIEvaluator(storage, model=model)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Get results to evaluate
    if prompt:
        results = storage.get_results_by_prompt(prompt)
        console.print(f"Loaded {len(results)} results for prompt '{prompt}'")
    else:
        results = storage.get_all_results()
        console.print(f"Loaded {len(results)} total results")

    # Filter out already AI-evaluated results
    unevaluated = []
    for result in results:
        evals = storage.get_evaluations_by_experiment(result.experiment_id)
        # Check if already has AI evaluation
        has_ai_eval = any(e.evaluation_type == "ai" for e in evals)
        if not has_ai_eval:
            unevaluated.append(result)

    console.print(f"Found {len(unevaluated)} unevaluated results\n")

    if not unevaluated:
        console.print("[yellow]No results to evaluate![/yellow]")
        return

    criteria_list = list(criteria) if criteria else None

    # Run AI evaluation with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(unevaluated))

        for result in unevaluated:
            progress.update(
                task,
                description=f"Evaluating: {result.prompt_name} + {result.config_name}"
            )

            ai_eval.evaluate_result(result, criteria=criteria_list)
            progress.advance(task)

    console.print("\n[bold green]AI evaluation complete![/bold green]")


@main.command()
@click.option(
    "--db",
    default=None,
    help="Database URL"
)
@click.option(
    "--prompt",
    help="Analyze specific prompt only"
)
@click.option(
    "--export",
    type=click.Path(),
    help="Export results to CSV file"
)
def analyze(db, prompt, export):
    """
    Analyze results and compare configurations.

    Show which configs performed best for each prompt.
    """
    console.print("[bold cyan]Benchmark Analysis[/bold cyan]\n")

    # Initialize storage and analyzer
    db_url = db or os.getenv("DATABASE_URL", "sqlite:///data/results/benchmark.db")
    storage = ResultStorage(db_url)
    analyzer = BenchmarkAnalyzer(storage)

    if prompt:
        # Analyze single prompt
        comparison = analyzer.analyze_prompt(prompt)
        analyzer.print_comparison(comparison)
    else:
        # Analyze all prompts
        comparisons = analyzer.analyze_all_prompts()

        for comparison in comparisons.values():
            analyzer.print_comparison(comparison)
            console.print("\n" + "="*80 + "\n")

        # Show overall rankings
        rankings = analyzer.get_overall_rankings()
        analyzer.print_overall_rankings(rankings)

    # Export to CSV if requested
    if export:
        df = analyzer.export_to_dataframe()
        df.to_csv(export, index=False)
        console.print(f"\n[green]Results exported to: {export}[/green]")


@main.command()
def init():
    """
    Initialize the benchmark environment.

    Creates directories and example files to get started.
    """
    console.print("[bold cyan]Initializing Benchmark Environment[/bold cyan]\n")

    # Create directories
    dirs = [
        "data/prompts",
        "data/configs",
        "data/results"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created {dir_path}")

    # Save example prompts
    prompts = create_example_prompts()
    for name, prompt in prompts.items():
        PromptLoader.save_prompt_to_file(
            prompt,
            f"data/prompts/{name}.yaml"
        )
    console.print(f"[green]✓[/green] Created {len(prompts)} example prompts")

    # Save example configs
    configs = create_default_configs()
    for name, config in configs.items():
        ConfigLoader.save_config_to_file(
            config,
            f"data/configs/{name}.json"
        )
    console.print(f"[green]✓[/green] Created {len(configs)} example configs")

    # Create .env if it doesn't exist
    if not Path(".env").exists():
        import shutil
        shutil.copy(".env.example", ".env")
        console.print("[green]✓[/green] Created .env file")
        console.print("[yellow]⚠[/yellow]  Please edit .env and add your OPENAI_API_KEY")
    else:
        console.print("[yellow]⚠[/yellow]  .env already exists, skipping")

    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Edit .env and add your OPENAI_API_KEY")
    console.print("2. Review prompts in data/prompts/")
    console.print("3. Review configs in data/configs/")
    console.print("4. Run: benchmark run")


if __name__ == "__main__":
    main()
