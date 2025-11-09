"""
Ranking algorithms for comparing AI and human rankings.

Includes Kendall Tau correlation, Borda count consensus, and agreement metrics.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .models import AIEvaluation, HumanRanking


def calculate_agreement(
    ai_ranking: List[str],
    human_ranking: List[str]
) -> Dict[str, Any]:
    """
    Calculate agreement metrics between AI and human rankings.

    Uses Kendall Tau correlation and other metrics.

    Args:
        ai_ranking: Ordered list of experiment IDs (AI's ranking)
        human_ranking: Ordered list of experiment IDs (human's ranking)

    Returns:
        Dictionary with agreement metrics
    """
    # Kendall Tau: measures rank correlation
    tau = calculate_kendall_tau(ai_ranking, human_ranking)

    # Top-3 overlap: how many of top 3 are the same
    top_3_ai = set(ai_ranking[:3])
    top_3_human = set(human_ranking[:3])
    top_3_overlap = len(top_3_ai & top_3_human)

    # Exact position matches
    exact_matches = sum(
        1 for i in range(len(ai_ranking))
        if i < len(human_ranking) and ai_ranking[i] == human_ranking[i]
    )

    # Track all position changes
    changes = []
    for exp_id in ai_ranking:
        if exp_id in human_ranking:
            ai_pos = ai_ranking.index(exp_id) + 1
            human_pos = human_ranking.index(exp_id) + 1
            if ai_pos != human_pos:
                changes.append({
                    "experiment_id": exp_id,
                    "from_rank": ai_pos,
                    "to_rank": human_pos,
                    "direction": "up" if human_pos < ai_pos else "down",
                    "magnitude": abs(human_pos - ai_pos)
                })

    return {
        "kendall_tau": tau,
        "top_3_overlap": top_3_overlap,
        "exact_position_matches": exact_matches,
        "agreement_percentage": (exact_matches / len(ai_ranking)) * 100 if ai_ranking else 0,
        "changes": changes,
        "num_changes": len(changes)
    }


def calculate_kendall_tau(ranking1: List[str], ranking2: List[str]) -> float:
    """
    Kendall Tau correlation coefficient.

    Measures ordinal association between two rankings.
    Returns value between -1 (complete disagreement) and 1 (complete agreement).

    Args:
        ranking1: First ranking (ordered list)
        ranking2: Second ranking (ordered list)

    Returns:
        Tau value between -1 and 1
    """
    # Find common items
    common_items = set(ranking1) & set(ranking2)

    if len(common_items) < 2:
        return 0.0

    # Filter both rankings to only common items
    filtered1 = [item for item in ranking1 if item in common_items]
    filtered2 = [item for item in ranking2 if item in common_items]

    n = len(filtered1)
    concordant = 0
    discordant = 0

    # Create position maps
    pos1 = {item: i for i, item in enumerate(filtered1)}
    pos2 = {item: i for i, item in enumerate(filtered2)}

    # Count concordant and discordant pairs
    for i in range(n):
        for j in range(i + 1, n):
            item_i = filtered1[i]
            item_j = filtered1[j]

            # Check if pair is concordant or discordant
            if (pos2[item_i] < pos2[item_j]):
                concordant += 1
            else:
                discordant += 1

    # Calculate tau
    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 0.0

    tau = (concordant - discordant) / total_pairs
    return tau


def calculate_consensus_ranking(
    rankings: List[HumanRanking],
    ai_ranking: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate consensus from multiple human rankings using Borda count.

    Each ranker assigns points: n points for 1st place, n-1 for 2nd, etc.
    Sum points for each item to get consensus ranking.

    Args:
        rankings: List of HumanRanking objects
        ai_ranking: Optional AI ranking for comparison

    Returns:
        Dictionary with consensus ranking and metrics, or None if no rankings
    """
    if not rankings:
        return None

    # Initialize scores
    scores = defaultdict(float)
    n = len(rankings[0].ranked_experiment_ids)

    # Borda count
    for ranking in rankings:
        for position, exp_id in enumerate(ranking.ranked_experiment_ids):
            points = n - position  # Higher position = more points
            scores[exp_id] += points

    # Sort by score (descending)
    consensus = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Calculate agreement with AI if provided
    ai_agreement = None
    if ai_ranking:
        ai_agreement = calculate_agreement(ai_ranking, consensus)

    # Calculate variability (how much humans disagree)
    variability = calculate_ranking_variability(rankings)

    return {
        "consensus_ranking": consensus,
        "confidence_scores": dict(scores),
        "num_rankers": len(rankings),
        "ai_agreement": ai_agreement,
        "variability": variability
    }


def calculate_ranking_variability(rankings: List[HumanRanking]) -> str:
    """
    Calculate how much humans disagree in their rankings.

    Args:
        rankings: List of HumanRanking objects

    Returns:
        "low", "medium", or "high" variability
    """
    if len(rankings) < 2:
        return "low"

    # Calculate pairwise Kendall Tau between all rankings
    taus = []
    for i in range(len(rankings)):
        for j in range(i + 1, len(rankings)):
            tau = calculate_kendall_tau(
                rankings[i].ranked_experiment_ids,
                rankings[j].ranked_experiment_ids
            )
            taus.append(tau)

    if not taus:
        return "low"

    avg_tau = sum(taus) / len(taus)

    # Classify variability
    if avg_tau >= 0.7:
        return "low"  # High agreement
    elif avg_tau >= 0.4:
        return "medium"
    else:
        return "high"  # Low agreement


def calculate_ranking_variance(rankings: List[HumanRanking], config_name: str) -> float:
    """
    Calculate variance in position for a specific config across rankings.

    Args:
        rankings: List of HumanRanking objects
        config_name: Configuration name to check

    Returns:
        Variance in position (lower = more agreement)
    """
    positions = []
    for ranking in rankings:
        if config_name in ranking.ranked_experiment_ids:
            pos = ranking.ranked_experiment_ids.index(config_name)
            positions.append(pos)

    if len(positions) < 2:
        return 0.0

    mean_pos = sum(positions) / len(positions)
    variance = sum((pos - mean_pos) ** 2 for pos in positions) / len(positions)
    return variance
