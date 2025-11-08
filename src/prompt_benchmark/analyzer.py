"""
Analyzer for comparing configurations and generating reports.

Analyzes experiment results to determine which configs perform best.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.table import Table

from .models import ConfigComparison, Evaluation, ExperimentResult
from .storage import ResultStorage


console = Console()


class BenchmarkAnalyzer:
    """
    Analyze experiment results and compare configurations.

    Provides statistical analysis and rankings of different configs.
    """

    def __init__(self, storage: ResultStorage):
        """
        Initialize the analyzer.

        Args:
            storage: Storage instance for loading results and evaluations
        """
        self.storage = storage

    def analyze_prompt(
        self,
        prompt_name: str,
        include_unevaluated: bool = False
    ) -> ConfigComparison:
        """
        Analyze all configs for a specific prompt.

        Args:
            prompt_name: Name of the prompt to analyze
            include_unevaluated: Include results without evaluations

        Returns:
            ConfigComparison with rankings and statistics
        """
        # Get all results for this prompt
        results = self.storage.get_results_by_prompt(prompt_name)

        if not results:
            return ConfigComparison(
                prompt_name=prompt_name,
                total_experiments=0,
                total_evaluations=0
            )

        # Get evaluations for all these results
        all_evaluations = {}
        for result in results:
            evals = self.storage.get_evaluations_by_experiment(result.experiment_id)
            if evals:
                all_evaluations[result.experiment_id] = evals

        # Group results by config
        config_results: Dict[str, List[ExperimentResult]] = defaultdict(list)
        for result in results:
            config_results[result.config_name].append(result)

        # Calculate statistics for each config
        config_stats = {}
        for config_name, config_result_list in config_results.items():
            stats = self._calculate_config_stats(
                config_result_list,
                all_evaluations,
                include_unevaluated
            )
            config_stats[config_name] = stats

        # Determine best configs
        best_by_score = self._get_best_by_metric(config_stats, "avg_score")
        best_by_speed = self._get_best_by_metric(config_stats, "avg_duration", minimize=True)
        best_by_cost = self._get_best_by_metric(config_stats, "avg_cost", minimize=True)

        total_evaluations = sum(len(evals) for evals in all_evaluations.values())

        return ConfigComparison(
            prompt_name=prompt_name,
            best_by_score=best_by_score,
            best_by_speed=best_by_speed,
            best_by_cost=best_by_cost,
            config_stats=config_stats,
            total_experiments=len(results),
            total_evaluations=total_evaluations
        )

    def analyze_all_prompts(
        self,
        include_unevaluated: bool = False
    ) -> Dict[str, ConfigComparison]:
        """
        Analyze all prompts.

        Args:
            include_unevaluated: Include results without evaluations

        Returns:
            Dictionary mapping prompt names to ConfigComparisons
        """
        # Get all unique prompt names
        all_results = self.storage.get_all_results()
        prompt_names = set(r.prompt_name for r in all_results)

        # Analyze each prompt
        comparisons = {}
        for prompt_name in prompt_names:
            comparisons[prompt_name] = self.analyze_prompt(
                prompt_name,
                include_unevaluated
            )

        return comparisons

    def get_overall_rankings(
        self,
        include_unevaluated: bool = False
    ) -> Dict[str, Dict]:
        """
        Get overall config rankings across all prompts.

        Args:
            include_unevaluated: Include results without evaluations

        Returns:
            Dictionary with overall statistics per config
        """
        all_results = self.storage.get_all_results()
        all_evaluations_list = self.storage.get_all_evaluations()

        # Build evaluation lookup
        eval_lookup = defaultdict(list)
        for eval in all_evaluations_list:
            eval_lookup[eval.experiment_id].append(eval)

        # Group by config across all prompts
        config_results: Dict[str, List[ExperimentResult]] = defaultdict(list)
        for result in all_results:
            config_results[result.config_name].append(result)

        # Calculate overall statistics
        overall_stats = {}
        for config_name, results_list in config_results.items():
            stats = self._calculate_config_stats(
                results_list,
                eval_lookup,
                include_unevaluated
            )
            overall_stats[config_name] = stats

        return overall_stats

    def _calculate_config_stats(
        self,
        results: List[ExperimentResult],
        evaluations_map: Dict[str, List[Evaluation]],
        include_unevaluated: bool
    ) -> Dict:
        """
        Calculate statistics for a config's results.

        Args:
            results: List of results for this config
            evaluations_map: Map of experiment_id to evaluations
            include_unevaluated: Include results without evaluations

        Returns:
            Dictionary of statistics
        """
        # Filter to successful results
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {
                "count": 0,
                "success_rate": 0.0
            }

        # Collect metrics
        durations = [r.duration_seconds for r in successful_results]
        costs = [r.estimated_cost_usd for r in successful_results if r.estimated_cost_usd]
        tokens = [r.total_tokens for r in successful_results if r.total_tokens]

        # Collect scores from evaluations
        scores = []
        for result in successful_results:
            evals = evaluations_map.get(result.experiment_id, [])
            for eval in evals:
                scores.append(eval.score)

        # Calculate statistics
        stats = {
            "count": len(successful_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0,
            "avg_duration": sum(durations) / len(durations) if durations else None,
            "min_duration": min(durations) if durations else None,
            "max_duration": max(durations) if durations else None,
            "avg_cost": sum(costs) / len(costs) if costs else None,
            "total_cost": sum(costs) if costs else None,
            "avg_tokens": sum(tokens) / len(tokens) if tokens else None,
            "total_tokens": sum(tokens) if tokens else None,
        }

        # Add evaluation statistics
        if scores or include_unevaluated:
            stats["avg_score"] = sum(scores) / len(scores) if scores else None
            stats["min_score"] = min(scores) if scores else None
            stats["max_score"] = max(scores) if scores else None
            stats["num_evaluations"] = len(scores)

        return stats

    def _get_best_by_metric(
        self,
        config_stats: Dict[str, Dict],
        metric: str,
        minimize: bool = False
    ) -> Optional[str]:
        """
        Find the best config by a specific metric.

        Args:
            config_stats: Statistics for each config
            metric: Metric name to compare
            minimize: If True, lower is better; if False, higher is better

        Returns:
            Name of the best config, or None if no data
        """
        valid_configs = {
            name: stats[metric]
            for name, stats in config_stats.items()
            if stats.get(metric) is not None
        }

        if not valid_configs:
            return None

        if minimize:
            return min(valid_configs, key=valid_configs.get)
        else:
            return max(valid_configs, key=valid_configs.get)

    def print_comparison(self, comparison: ConfigComparison) -> None:
        """
        Print a formatted comparison table.

        Args:
            comparison: ConfigComparison to display
        """
        console.print(f"\n[bold cyan]Analysis for Prompt: {comparison.prompt_name}[/bold cyan]")
        console.print(f"Total Experiments: {comparison.total_experiments}")
        console.print(f"Total Evaluations: {comparison.total_evaluations}\n")

        if comparison.best_by_score:
            console.print(f"[green]Best by Score:[/green] {comparison.best_by_score}")
        if comparison.best_by_speed:
            console.print(f"[yellow]Best by Speed:[/yellow] {comparison.best_by_speed}")
        if comparison.best_by_cost:
            console.print(f"[blue]Best by Cost:[/blue] {comparison.best_by_cost}")

        # Create detailed table
        table = Table(title=f"\nConfig Statistics for '{comparison.prompt_name}'")
        table.add_column("Config", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Avg Score", justify="right")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Avg Cost ($)", justify="right")
        table.add_column("Avg Tokens", justify="right")

        for config_name, stats in comparison.config_stats.items():
            table.add_row(
                config_name,
                str(stats.get("count", 0)),
                f"{stats.get('avg_score', 0):.2f}" if stats.get("avg_score") else "N/A",
                f"{stats.get('avg_duration', 0):.2f}" if stats.get("avg_duration") else "N/A",
                f"{stats.get('avg_cost', 0):.6f}" if stats.get("avg_cost") else "N/A",
                str(int(stats.get("avg_tokens", 0))) if stats.get("avg_tokens") else "N/A"
            )

        console.print(table)

    def print_overall_rankings(self, rankings: Dict[str, Dict]) -> None:
        """
        Print overall rankings across all prompts.

        Args:
            rankings: Overall statistics per config
        """
        console.print("\n[bold cyan]Overall Config Rankings (All Prompts)[/bold cyan]\n")

        table = Table(title="Overall Statistics")
        table.add_column("Config", style="cyan")
        table.add_column("Total Runs", justify="right")
        table.add_column("Avg Score", justify="right")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Total Cost ($)", justify="right")
        table.add_column("Total Tokens", justify="right")

        # Sort by average score (descending)
        sorted_configs = sorted(
            rankings.items(),
            key=lambda x: x[1].get("avg_score", 0) or 0,
            reverse=True
        )

        for config_name, stats in sorted_configs:
            table.add_row(
                config_name,
                str(stats.get("count", 0)),
                f"{stats.get('avg_score', 0):.2f}" if stats.get("avg_score") else "N/A",
                f"{stats.get('avg_duration', 0):.2f}" if stats.get("avg_duration") else "N/A",
                f"{stats.get('total_cost', 0):.4f}" if stats.get('total_cost') else "N/A",
                str(int(stats.get("total_tokens", 0))) if stats.get("total_tokens") else "N/A"
            )

        console.print(table)

    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Export all results to a pandas DataFrame for analysis.

        Returns:
            DataFrame with all experiment results and evaluations
        """
        results = self.storage.get_all_results()
        evaluations = self.storage.get_all_evaluations()

        # Build evaluation lookup
        eval_map = defaultdict(list)
        for eval in evaluations:
            eval_map[eval.experiment_id].append(eval)

        # Build rows
        rows = []
        for result in results:
            base_row = {
                "experiment_id": result.experiment_id,
                "prompt_name": result.prompt_name,
                "config_name": result.config_name,
                "model": result.config.model,
                "temperature": result.config.temperature,
                "max_tokens": result.config.max_output_tokens,
                "duration_seconds": result.duration_seconds,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "estimated_cost_usd": result.estimated_cost_usd,
                "success": result.success,
                "error": result.error,
            }

            # Add evaluation data
            evals = eval_map.get(result.experiment_id, [])
            if evals:
                for eval in evals:
                    row = base_row.copy()
                    row.update({
                        "evaluation_type": eval.evaluation_type,
                        "evaluator_name": eval.evaluator_name,
                        "score": eval.score,
                        "notes": eval.notes,
                    })
                    rows.append(row)
            else:
                rows.append(base_row)

        return pd.DataFrame(rows)
