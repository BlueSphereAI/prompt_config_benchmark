"""
Recommendation engine for determining best LLM configurations.

Combines quality scores, speed, and cost with configurable weights to recommend
the optimal configuration for a given prompt.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import (
    AIEvaluation,
    ExperimentResult,
    HumanRanking,
    RankingWeights,
    Recommendation,
)
from .ranker import calculate_consensus_ranking, calculate_ranking_variance
from .storage import ResultStorage


def calculate_recommendation(
    prompt_name: str,
    storage: ResultStorage,
    weights: Optional[RankingWeights] = None
) -> Recommendation:
    """
    Calculate best config recommendation based on weighted scoring.

    Default weights: quality 60%, speed 30%, cost 10%

    Args:
        prompt_name: Name of the prompt
        storage: Database storage instance
        weights: Optional custom weights (uses defaults if None)

    Returns:
        Recommendation object with best config and reasoning
    """
    # Get weights (use defaults if not provided)
    if weights is None:
        weights = storage.get_weights(prompt_name) or RankingWeights(
            prompt_name=prompt_name,
            quality_weight=0.60,
            speed_weight=0.30,
            cost_weight=0.10,
            updated_by="system"
        )

    # Get all data
    experiments = storage.get_results_by_prompt(prompt_name, success_only=True)
    ai_evals = storage.get_ai_evaluations_by_prompt(prompt_name)
    human_rankings = storage.get_human_rankings_by_prompt(prompt_name)

    if not experiments:
        raise ValueError(f"No successful experiments found for prompt: {prompt_name}")

    # Group by config
    config_groups = defaultdict(list)
    for exp in experiments:
        config_groups[exp.config_name].append(exp)

    # Calculate scores for each config
    config_scores = {}
    all_durations = [e.duration_seconds for e in experiments]
    all_costs = [e.estimated_cost_usd for e in experiments if e.estimated_cost_usd is not None]

    max_duration = max(all_durations) if all_durations else 1.0
    max_cost = max(all_costs) if all_costs else 1.0

    for config_name, exps in config_groups.items():
        # Quality score (from evaluations)
        quality = calculate_quality_score(config_name, ai_evals, human_rankings, experiments)

        # Speed score (normalized, inverted - faster is better)
        avg_duration = sum(e.duration_seconds for e in exps) / len(exps)
        speed = 10 * (1 - (avg_duration / max_duration)) if max_duration > 0 else 5.0

        # Cost score (normalized, inverted - cheaper is better)
        costs = [e.estimated_cost_usd for e in exps if e.estimated_cost_usd is not None]
        if costs:
            avg_cost = sum(costs) / len(costs)
            cost = 10 * (1 - (avg_cost / max_cost)) if max_cost > 0 else 5.0
        else:
            cost = 5.0  # Neutral if no cost data

        # Weighted final score
        final_score = (
            quality * weights.quality_weight +
            speed * weights.speed_weight +
            cost * weights.cost_weight
        )

        config_scores[config_name] = {
            "final_score": final_score,
            "quality_score": quality,
            "speed_score": speed,
            "cost_score": cost
        }

    # Find best config
    best_config = max(config_scores.keys(), key=lambda k: config_scores[k]["final_score"])

    # Calculate confidence
    confidence, confidence_factors = calculate_confidence(
        best_config, ai_evals, human_rankings, experiments
    )

    # Get consensus agreement if multiple humans
    consensus_agreement = None
    if len(human_rankings) > 1:
        consensus = calculate_consensus_ranking(human_rankings)
        if consensus and best_config in consensus["consensus_ranking"]:
            # How close to top of consensus?
            consensus_pos = consensus["consensus_ranking"].index(best_config)
            consensus_agreement = 1.0 - (consensus_pos / len(consensus["consensus_ranking"]))

    # Generate reasoning
    reasoning = generate_reasoning(
        best_config,
        config_scores,
        config_groups,
        ai_evals,
        human_rankings
    )

    # Find runner-up
    sorted_configs = sorted(
        config_scores.keys(),
        key=lambda k: config_scores[k]["final_score"],
        reverse=True
    )
    runner_up = sorted_configs[1] if len(sorted_configs) > 1 else None
    score_diff = (
        config_scores[best_config]["final_score"] - config_scores[runner_up]["final_score"]
        if runner_up else 0
    )

    return Recommendation(
        prompt_name=prompt_name,
        recommended_config=best_config,
        final_score=config_scores[best_config]["final_score"],
        quality_score=config_scores[best_config]["quality_score"],
        speed_score=config_scores[best_config]["speed_score"],
        cost_score=config_scores[best_config]["cost_score"],
        confidence=confidence,
        confidence_factors=confidence_factors,
        num_ai_evaluations=len(ai_evals),
        num_human_rankings=len(human_rankings),
        consensus_agreement=consensus_agreement,
        reasoning=reasoning,
        runner_up_config=runner_up,
        score_difference=score_diff,
        generated_at=datetime.utcnow()
    )


def calculate_quality_score(
    config_name: str,
    ai_evals: List[AIEvaluation],
    human_rankings: List[HumanRanking],
    all_experiments: List[ExperimentResult]
) -> float:
    """
    Calculate quality score from AI evaluations and human rankings.

    Priority:
    1. If human rankings exist, use consensus
    2. Otherwise, use AI evaluation
    3. Otherwise, return 5.0 (neutral)

    Args:
        config_name: Configuration name
        ai_evals: List of AI evaluations
        human_rankings: List of human rankings
        all_experiments: All experiments for normalizing positions

    Returns:
        Quality score from 0-10
    """
    # Find evaluations for this config (match by config name in experiment_id)
    config_ai_evals = [
        e for e in ai_evals
        if any(exp.experiment_id == e.experiment_id and exp.config_name == config_name
               for exp in all_experiments)
    ]

    if human_rankings:
        # Use human consensus
        # Convert rankings to scores (1st = 10, 2nd = 9, etc.)
        scores = []
        for ranking in human_rankings:
            # Find experiment IDs for this config
            config_exp_ids = [
                exp.experiment_id for exp in all_experiments
                if exp.config_name == config_name
            ]

            for exp_id in config_exp_ids:
                if exp_id in ranking.ranked_experiment_ids:
                    position = ranking.ranked_experiment_ids.index(exp_id)
                    num_items = len(ranking.ranked_experiment_ids)
                    # Convert position to score (lower position = higher score)
                    score = 10 * (1 - (position / num_items)) if num_items > 0 else 5.0
                    scores.append(score)

        return sum(scores) / len(scores) if scores else 5.0

    elif config_ai_evals:
        # Use AI evaluation
        return sum(e.overall_score for e in config_ai_evals) / len(config_ai_evals)

    else:
        # No evaluations yet
        return 5.0


def calculate_confidence(
    config_name: str,
    ai_evals: List[AIEvaluation],
    human_rankings: List[HumanRanking],
    all_experiments: List[ExperimentResult]
) -> Tuple[str, List[str]]:
    """
    Determine confidence level and factors.

    Returns: ("HIGH"|"MEDIUM"|"LOW", [list of reasons])

    Args:
        config_name: Configuration being evaluated
        ai_evals: List of AI evaluations
        human_rankings: List of human rankings
        all_experiments: All experiments

    Returns:
        Tuple of (confidence level, confidence factors)
    """
    factors = []
    score = 0

    # Check for AI evaluations
    if ai_evals:
        score += 1
        factors.append("AI evaluation available")

    # Check for human rankings
    if human_rankings:
        score += 2
        factors.append(f"{len(human_rankings)} human ranking(s)")

        # Check for agreement between humans
        if len(human_rankings) > 1:
            # Calculate variance
            variance = calculate_ranking_variance(human_rankings, config_name)
            if variance < 1.0:
                score += 1
                factors.append("High human agreement")
            else:
                factors.append("Some human disagreement")

    # Check AI-human agreement
    if ai_evals and human_rankings:
        # Check if humans agreed with AI
        consensus = calculate_consensus_ranking(human_rankings)
        if consensus:
            # Find experiments for this config
            config_exp_ids = [
                exp.experiment_id for exp in all_experiments
                if exp.config_name == config_name
            ]
            # Check if any are at top of consensus
            if config_exp_ids and config_exp_ids[0] in consensus["consensus_ranking"][:2]:
                score += 1
                factors.append("Humans confirm AI ranking")

    # Determine confidence
    if score >= 4:
        confidence = "HIGH"
    elif score >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
        if not human_rankings:
            factors.append("No human rankings yet")

    return confidence, factors


def generate_reasoning(
    best_config: str,
    config_scores: Dict[str, Dict[str, float]],
    config_groups: Dict[str, List[ExperimentResult]],
    ai_evals: List[AIEvaluation],
    human_rankings: List[HumanRanking]
) -> str:
    """
    Generate human-readable explanation for recommendation.

    Args:
        best_config: The recommended configuration
        config_scores: Scores for all configurations
        config_groups: Experiments grouped by config
        ai_evals: AI evaluations
        human_rankings: Human rankings

    Returns:
        Human-readable reasoning string
    """
    scores = config_scores[best_config]
    exps = config_groups[best_config]

    # Calculate averages
    avg_duration = sum(e.duration_seconds for e in exps) / len(exps)
    costs = [e.estimated_cost_usd for e in exps if e.estimated_cost_usd is not None]
    avg_cost = sum(costs) / len(costs) if costs else 0

    # Build reasoning
    parts = []

    # Quality
    parts.append(
        f"{best_config} achieved {'the highest' if scores['quality_score'] >= 8 else 'a strong'} "
        f"quality score ({scores['quality_score']:.1f}/10)"
    )

    # Human validation
    if human_rankings:
        num_humans = len(human_rankings)
        parts.append(
            f"and was ranked highly by {num_humans} human evaluator{'s' if num_humans > 1 else ''}"
        )

    # Performance characteristics
    parts.append(
        f"It offers balanced performance with {avg_duration:.1f}s duration"
    )

    if avg_cost > 0:
        parts.append(f"and ${avg_cost:.4f} cost")

    reasoning = ". ".join(parts) + "."

    return reasoning
