"""API routes for benchmark results viewer."""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import Integer, func, text

from prompt_benchmark.storage import ResultStorage, DBExperimentResult, DBEvaluation
from prompt_benchmark.analyzer import BenchmarkAnalyzer
from prompt_benchmark.models import Evaluation, ReviewPrompt, HumanRanking, RankingWeights, Prompt, ExperimentRun
from prompt_benchmark.evaluator import run_batch_evaluation
from prompt_benchmark.recommender import calculate_recommendation
from prompt_benchmark.ranker import calculate_agreement
from prompt_benchmark.executor import ExperimentExecutor
from prompt_benchmark.config_loader import ConfigLoader
from prompt_benchmark.api.schemas import (
    ExperimentResponse,
    EvaluationResponse,
    EvaluationCreate,
    ExperimentAcceptabilityUpdate,
    ConfigComparison,
    OverallRankings,
    DashboardStats,
    LLMConfigResponse,
    LLMConfigCreate,
    LLMConfigUpdate,
    ExperimentRunResponse,
    RunWithExperimentsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Track running experiments
running_experiments: set[str] = set()


def get_storage() -> ResultStorage:
    """Dependency to get storage instance."""
    return ResultStorage()


def get_analyzer(storage: ResultStorage = Depends(get_storage)) -> BenchmarkAnalyzer:
    """Dependency to get analyzer instance."""
    return BenchmarkAnalyzer(storage)


@router.get("/experiments", response_model=List[ExperimentResponse])
def get_experiments(
    prompt_name: Optional[str] = Query(None),
    config_name: Optional[str] = Query(None),
    success_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    storage: ResultStorage = Depends(get_storage),
):
    """Get list of experiments with optional filtering."""
    with SQLSession(storage.engine) as session:
        query = session.query(DBExperimentResult)

        if prompt_name:
            query = query.filter(DBExperimentResult.prompt_name == prompt_name)

        if config_name:
            query = query.filter(DBExperimentResult.config_name == config_name)

        if success_only:
            query = query.filter(DBExperimentResult.success == True)

        # Order by created_at descending (most recent first)
        query = query.order_by(DBExperimentResult.created_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        results = query.all()

        # Convert to response models
        experiments = []
        for result in results:
            exp_dict = {
                "id": result.id,
                "experiment_id": result.experiment_id,
                "prompt_name": result.prompt_name,
                "config_name": result.config_name,
                "rendered_prompt": result.rendered_prompt,
                "config_json": json.loads(result.config_json) if result.config_json else {},
                "response": result.response or "",
                "finish_reason": result.finish_reason,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "duration_seconds": result.duration_seconds,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "estimated_cost_usd": result.estimated_cost_usd,
                "error": result.error,
                "success": result.success,
                "is_acceptable": result.is_acceptable,
                "metadata_json": json.loads(result.metadata_json) if result.metadata_json else None,
                "created_at": result.created_at,
            }
            experiments.append(ExperimentResponse(**exp_dict))

        return experiments


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get a single experiment by ID."""
    with SQLSession(storage.engine) as session:
        db_result = session.query(DBExperimentResult).filter(
            DBExperimentResult.experiment_id == experiment_id
        ).first()

        if not db_result:
            raise HTTPException(status_code=404, detail="Experiment not found")

        exp_dict = {
            "id": db_result.id,
            "experiment_id": db_result.experiment_id,
            "prompt_name": db_result.prompt_name,
            "config_name": db_result.config_name,
            "rendered_prompt": db_result.rendered_prompt,
            "config_json": json.loads(db_result.config_json) if db_result.config_json else {},
            "response": db_result.response or "",
            "finish_reason": db_result.finish_reason,
            "start_time": db_result.start_time,
            "end_time": db_result.end_time,
            "duration_seconds": db_result.duration_seconds,
            "prompt_tokens": db_result.prompt_tokens,
            "completion_tokens": db_result.completion_tokens,
            "total_tokens": db_result.total_tokens,
            "estimated_cost_usd": db_result.estimated_cost_usd,
            "error": db_result.error,
            "success": db_result.success,
            "is_acceptable": db_result.is_acceptable,
            "metadata_json": json.loads(db_result.metadata_json) if db_result.metadata_json else None,
            "created_at": db_result.created_at,
        }

        return ExperimentResponse(**exp_dict)


@router.put("/experiments/{experiment_id}/acceptability")
def update_experiment_acceptability(
    experiment_id: str,
    update: ExperimentAcceptabilityUpdate,
    storage: ResultStorage = Depends(get_storage),
):
    """Update the acceptability status of an experiment."""
    success = storage.update_experiment_acceptability(experiment_id, update.is_acceptable)

    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return {"success": True, "experiment_id": experiment_id, "is_acceptable": update.is_acceptable}


@router.get("/prompts", response_model=List[str])
def get_prompts(storage: ResultStorage = Depends(get_storage)):
    """Get list of distinct prompt names."""
    with SQLSession(storage.engine) as session:
        prompts = session.query(DBExperimentResult.prompt_name).distinct().all()
        return [p[0] for p in prompts]


@router.get("/configs", response_model=List[str])
def get_configs(storage: ResultStorage = Depends(get_storage)):
    """Get list of distinct config names."""
    with SQLSession(storage.engine) as session:
        configs = session.query(DBExperimentResult.config_name).distinct().all()
        return [c[0] for c in configs]


@router.get("/analysis/prompt/{prompt_name}", response_model=ConfigComparison)
def analyze_prompt(
    prompt_name: str,
    include_unevaluated: bool = Query(True),
    analyzer: BenchmarkAnalyzer = Depends(get_analyzer),
):
    """Get analysis for a specific prompt."""
    comparison = analyzer.analyze_prompt(prompt_name, include_unevaluated)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"No results found for prompt: {prompt_name}")

    # Convert to response model
    return ConfigComparison(
        prompt_name=comparison.prompt_name,
        best_by_score=comparison.best_by_score,
        best_by_speed=comparison.best_by_speed,
        best_by_cost=comparison.best_by_cost,
        config_stats=comparison.config_stats,
        total_experiments=comparison.total_experiments,
        total_evaluations=comparison.total_evaluations,
    )


@router.get("/analysis/overall", response_model=OverallRankings)
def analyze_overall(
    include_unevaluated: bool = Query(True),
    analyzer: BenchmarkAnalyzer = Depends(get_analyzer),
):
    """Get overall rankings across all prompts."""
    config_stats = analyzer.get_overall_rankings(include_unevaluated)

    # Calculate totals from the config stats
    total_experiments = sum(stats.get("count", 0) for stats in config_stats.values())
    total_evaluations = sum(stats.get("num_evaluations", 0) for stats in config_stats.values())

    return OverallRankings(
        config_stats=config_stats,
        total_experiments=total_experiments,
        total_evaluations=total_evaluations,
    )


@router.get("/evaluations/{experiment_id}", response_model=List[EvaluationResponse])
def get_evaluations_for_experiment(
    experiment_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get all evaluations for a specific experiment."""
    with SQLSession(storage.engine) as session:
        evaluations = session.query(DBEvaluation).filter(
            DBEvaluation.experiment_id == experiment_id
        ).all()

        eval_list = []
        for ev in evaluations:
            eval_dict = {
                "id": ev.id,
                "evaluation_id": ev.evaluation_id,
                "experiment_id": ev.experiment_id,
                "result_id": ev.result_id,
                "evaluation_type": ev.evaluation_type,
                "evaluator_name": ev.evaluator_name,
                "score": ev.score,
                "criteria_json": json.loads(ev.criteria_json) if ev.criteria_json else None,
                "notes": ev.notes,
                "strengths": ev.strengths,
                "weaknesses": ev.weaknesses,
                "evaluated_at": ev.evaluated_at,
                "metadata_json": json.loads(ev.metadata_json) if ev.metadata_json else None,
            }
            eval_list.append(EvaluationResponse(**eval_dict))

        return eval_list


@router.post("/evaluations", response_model=EvaluationResponse)
def create_evaluation(
    evaluation: EvaluationCreate,
    storage: ResultStorage = Depends(get_storage),
):
    """Create a new evaluation for an experiment."""
    # Create Evaluation model
    eval_model = Evaluation(
        experiment_id=evaluation.experiment_id,
        evaluation_type=evaluation.evaluation_type,
        evaluator_name=evaluation.evaluator_name,
        score=evaluation.score,
        criteria=evaluation.criteria,
        notes=evaluation.notes,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        metadata=evaluation.metadata,
    )

    # Save to database
    storage.save_evaluation(eval_model)

    # Fetch the saved evaluation to return
    with SQLSession(storage.engine) as session:
        saved_eval = session.query(DBEvaluation).filter(
            DBEvaluation.evaluation_id == eval_model.evaluation_id
        ).first()

        if not saved_eval:
            raise HTTPException(status_code=500, detail="Failed to save evaluation")

        eval_dict = {
            "id": saved_eval.id,
            "evaluation_id": saved_eval.evaluation_id,
            "experiment_id": saved_eval.experiment_id,
            "result_id": saved_eval.result_id,
            "evaluation_type": saved_eval.evaluation_type,
            "evaluator_name": saved_eval.evaluator_name,
            "score": saved_eval.score,
            "criteria_json": json.loads(saved_eval.criteria_json) if saved_eval.criteria_json else None,
            "notes": saved_eval.notes,
            "strengths": saved_eval.strengths,
            "weaknesses": saved_eval.weaknesses,
            "evaluated_at": saved_eval.evaluated_at,
            "metadata_json": json.loads(saved_eval.metadata_json) if saved_eval.metadata_json else None,
        }

        return EvaluationResponse(**eval_dict)


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    storage: ResultStorage = Depends(get_storage),
):
    """Get dashboard summary statistics."""
    with SQLSession(storage.engine) as session:
        # Get counts
        total_experiments = session.query(DBExperimentResult).count()
        total_prompts = session.query(DBExperimentResult.prompt_name).distinct().count()
        total_configs = session.query(DBExperimentResult.config_name).distinct().count()
        total_evaluations = session.query(DBEvaluation).count()

        # Get aggregates
        agg_results = session.query(
            func.sum(DBExperimentResult.estimated_cost_usd).label("total_cost"),
            func.avg(DBExperimentResult.duration_seconds).label("avg_duration"),
            func.sum(DBExperimentResult.success.cast(Integer)).label("successful_count"),
        ).first()

        total_cost = float(agg_results.total_cost or 0.0)
        avg_duration = float(agg_results.avg_duration or 0.0)
        success_rate = (agg_results.successful_count / total_experiments * 100) if total_experiments > 0 else 0.0

        # Get recent experiments (last 5)
        recent = session.query(DBExperimentResult).order_by(
            DBExperimentResult.created_at.desc()
        ).limit(5).all()

        recent_experiments = []
        for result in recent:
            exp_dict = {
                "id": result.id,
                "experiment_id": result.experiment_id,
                "prompt_name": result.prompt_name,
                "config_name": result.config_name,
                "rendered_prompt": result.rendered_prompt,
                "config_json": json.loads(result.config_json) if result.config_json else {},
                "response": result.response or "",
                "finish_reason": result.finish_reason,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "duration_seconds": result.duration_seconds,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "estimated_cost_usd": result.estimated_cost_usd,
                "error": result.error,
                "success": result.success,
                "metadata_json": json.loads(result.metadata_json) if result.metadata_json else None,
                "created_at": result.created_at,
            }
            recent_experiments.append(ExperimentResponse(**exp_dict))

        return DashboardStats(
            total_experiments=total_experiments,
            total_prompts=total_prompts,
            total_configs=total_configs,
            total_evaluations=total_evaluations,
            total_cost=total_cost,
            avg_duration=avg_duration,
            success_rate=success_rate,
            recent_experiments=recent_experiments,
        )


# ============================================================================
# AI-Assisted Ranking System Routes
# ============================================================================


@router.post("/review-prompts")
def create_review_prompt(
    name: str,
    template: str,
    criteria: List[str],
    default_model: str,
    created_by: str,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    storage: ResultStorage = Depends(get_storage),
):
    """Create a new review prompt template."""
    review_prompt = ReviewPrompt(
        prompt_id=str(uuid.uuid4()),
        name=name,
        description=description,
        template=template,
        system_prompt=system_prompt,
        criteria=criteria,
        default_model=default_model,
        created_by=created_by,
    )
    storage.save_review_prompt(review_prompt)
    return review_prompt


@router.get("/review-prompts")
def get_review_prompts(
    active_only: bool = Query(True),
    storage: ResultStorage = Depends(get_storage),
):
    """Get all review prompt templates."""
    return storage.get_all_review_prompts(active_only=active_only)


@router.get("/review-prompts/{prompt_id}")
def get_review_prompt(
    prompt_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get a specific review prompt template."""
    prompt = storage.get_review_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Review prompt not found")
    return prompt


@router.put("/review-prompts/{prompt_id}")
def update_review_prompt(
    prompt_id: str,
    name: Optional[str] = None,
    template: Optional[str] = None,
    criteria: Optional[List[str]] = None,
    default_model: Optional[str] = None,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    storage: ResultStorage = Depends(get_storage),
):
    """Update an existing review prompt template."""
    logger.info(f"Updating review prompt: {prompt_id}")

    # Get existing prompt
    existing = storage.get_review_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review prompt not found")

    # Update fields if provided
    if name is not None:
        existing.name = name
    if template is not None:
        existing.template = template
    if criteria is not None:
        existing.criteria = criteria
    if default_model is not None:
        existing.default_model = default_model
    if description is not None:
        existing.description = description
    if system_prompt is not None:
        existing.system_prompt = system_prompt

    # Update timestamp
    from datetime import datetime
    existing.updated_at = datetime.utcnow()

    # Save to storage
    storage.save_review_prompt(existing)

    logger.info(f"Successfully updated review prompt: {prompt_id}")
    return existing


@router.delete("/review-prompts/{prompt_id}")
def delete_review_prompt(
    prompt_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Delete a review prompt template (soft delete)."""
    logger.info(f"Deleting review prompt: {prompt_id}")

    # Get existing prompt
    existing = storage.get_review_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review prompt not found")

    # Soft delete by setting is_active to False
    existing.is_active = False
    from datetime import datetime
    existing.updated_at = datetime.utcnow()
    storage.save_review_prompt(existing)

    logger.info(f"Successfully deleted review prompt: {prompt_id}")
    return {"status": "deleted", "prompt_id": prompt_id}


@router.post("/review-prompts/{prompt_id}/duplicate")
def duplicate_review_prompt(
    prompt_id: str,
    new_name: str = Query(..., description="Name for the duplicated prompt"),
    storage: ResultStorage = Depends(get_storage),
):
    """Duplicate an existing review prompt with a new name."""
    logger.info(f"Duplicating review prompt {prompt_id} to {new_name}")

    # Get source prompt
    source = storage.get_review_prompt(prompt_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source review prompt not found")

    # Check if new name already exists
    all_prompts = storage.get_all_review_prompts(active_only=False)
    if any(p.name == new_name for p in all_prompts):
        raise HTTPException(status_code=400, detail=f"Review prompt with name '{new_name}' already exists")

    # Create new prompt with duplicated data
    new_prompt = ReviewPrompt(
        prompt_id=str(uuid.uuid4()),
        name=new_name,
        description=f"Copy of {source.name}" + (f": {source.description}" if source.description else ""),
        template=source.template,
        system_prompt=source.system_prompt,
        criteria=source.criteria.copy(),
        default_model=source.default_model,
        created_by="system",  # Could be enhanced to track actual user
    )

    storage.save_review_prompt(new_prompt)

    logger.info(f"Successfully duplicated review prompt: {prompt_id} -> {new_prompt.prompt_id}")
    return new_prompt


@router.post("/review-prompts/validate")
def validate_review_prompt_template(
    template: str,
    criteria: List[str],
    storage: ResultStorage = Depends(get_storage),
):
    """Validate a review prompt template."""
    logger.info("Validating review prompt template")

    errors = []
    warnings = []

    # Check for required variables
    required_vars = ["{original_prompt}", "{num_configs}", "{all_responses}"]
    for var in required_vars:
        if var not in template:
            errors.append(f"Missing required variable: {var}")

    # Check if template mentions JSON output format
    if "json" not in template.lower():
        warnings.append("Template should instruct AI to return JSON format")

    # Check if template mentions rankings
    if "rank" not in template.lower():
        warnings.append("Template should instruct AI to provide rankings")

    # Check if criteria are mentioned in template
    for criterion in criteria:
        if criterion.lower() not in template.lower():
            warnings.append(f"Criterion '{criterion}' not mentioned in template")

    # Check template length
    if len(template) < 100:
        warnings.append("Template is very short - may not provide enough guidance")
    elif len(template) > 5000:
        warnings.append("Template is very long - may increase API costs")

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "required_variables": required_vars,
        "found_variables": [var for var in required_vars if var in template]
    }


@router.get("/review-prompts/{prompt_id}/stats")
def get_review_prompt_stats(
    prompt_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get usage statistics for a review prompt."""
    logger.info(f"Getting stats for review prompt: {prompt_id}")

    # Check if prompt exists
    prompt = storage.get_review_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Review prompt not found")

    from prompt_benchmark.storage import DBAIEvaluationBatch, DBAIEvaluation
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import func, select

    with SQLSession(storage.engine) as session:
        # Count number of batches using this prompt
        batch_count = session.query(DBAIEvaluationBatch).filter(
            DBAIEvaluationBatch.review_prompt_id == prompt_id
        ).count()

        # Get most recent batch
        latest_batch = session.query(DBAIEvaluationBatch).filter(
            DBAIEvaluationBatch.review_prompt_id == prompt_id
        ).order_by(DBAIEvaluationBatch.started_at.desc()).first()

        last_used = latest_batch.started_at if latest_batch else None

        # Get average overall score from evaluations
        avg_score_result = session.query(
            func.avg(DBAIEvaluation.overall_score)
        ).filter(
            DBAIEvaluation.review_prompt_id == prompt_id
        ).first()

        avg_score = float(avg_score_result[0]) if avg_score_result[0] is not None else None

        # Count total evaluations
        total_evaluations = session.query(DBAIEvaluation).filter(
            DBAIEvaluation.review_prompt_id == prompt_id
        ).count()

        # Get unique prompts evaluated
        unique_prompts = session.query(DBAIEvaluationBatch.prompt_name).filter(
            DBAIEvaluationBatch.review_prompt_id == prompt_id
        ).distinct().count()

        return {
            "prompt_id": prompt_id,
            "usage_count": batch_count,
            "last_used": last_used,
            "total_evaluations": total_evaluations,
            "unique_prompts_evaluated": unique_prompts,
            "average_score": avg_score,
        }


@router.post("/ai-evaluate/batch")
def start_batch_evaluation(
    prompt_name: str,
    review_prompt_id: str,
    model_evaluator: str = "gpt-4-turbo",
    run_id: Optional[str] = Query(None, description="Filter to specific run"),
    parallel: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    storage: ResultStorage = Depends(get_storage),
):
    """Start a batch AI evaluation of all configs for a prompt."""
    # Get review prompt
    review_prompt = storage.get_review_prompt(review_prompt_id)
    if not review_prompt:
        raise HTTPException(status_code=404, detail="Review prompt not found")

    # Check if experiments exist (filter by run_id if provided)
    if run_id:
        experiments = storage.get_results_by_run(run_id)
        experiments = [exp for exp in experiments if exp.success]
    else:
        experiments = storage.get_results_by_prompt(prompt_name, success_only=True)

    if not experiments:
        raise HTTPException(
            status_code=404,
            detail=f"No successful experiments found for prompt: {prompt_name}"
        )

    # Run evaluation in background
    def run_evaluation():
        run_batch_evaluation(prompt_name, review_prompt, model_evaluator, storage, parallel, run_id)

    background_tasks.add_task(run_evaluation)

    return {
        "status": "started",
        "prompt_name": prompt_name,
        "num_experiments": len(experiments),
        "message": "Batch evaluation started in background"
    }


@router.get("/ai-evaluate/batch/{batch_id}")
def get_batch_status(
    batch_id: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get status of a batch AI evaluation."""
    batch = storage.get_ai_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/ai-evaluations/prompt/{prompt_name}")
def get_ai_evaluations(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get AI evaluations for a prompt."""
    evaluations = storage.get_ai_evaluations_by_prompt(prompt_name)
    return {
        "prompt_name": prompt_name,
        "num_evaluations": len(evaluations),
        "evaluations": evaluations
    }


@router.post("/rankings")
def save_ranking(
    prompt_name: str,
    evaluator_name: str,
    ranked_experiment_ids: List[str],
    based_on_ai_batch_id: Optional[str] = None,
    notes: Optional[str] = None,
    time_spent_seconds: float = 0.0,
    storage: ResultStorage = Depends(get_storage),
):
    """Save a human ranking."""
    # Calculate agreement with AI if available
    changes_from_ai = []
    ai_agreement_score = None
    top_3_overlap = None
    exact_position_matches = None

    if based_on_ai_batch_id:
        batch = storage.get_ai_batch(based_on_ai_batch_id)
        if batch:
            ai_ranking = batch.ranked_experiment_ids
            agreement = calculate_agreement(ai_ranking, ranked_experiment_ids)
            changes_from_ai = agreement["changes"]
            ai_agreement_score = agreement["kendall_tau"]
            top_3_overlap = agreement["top_3_overlap"]
            exact_position_matches = agreement["exact_position_matches"]

    ranking = HumanRanking(
        ranking_id=str(uuid.uuid4()),
        prompt_name=prompt_name,
        evaluator_name=evaluator_name,
        ranked_experiment_ids=ranked_experiment_ids,
        based_on_ai_batch_id=based_on_ai_batch_id,
        changes_from_ai=changes_from_ai,
        ai_agreement_score=ai_agreement_score,
        top_3_overlap=top_3_overlap,
        exact_position_matches=exact_position_matches,
        notes=notes,
        time_spent_seconds=time_spent_seconds,
    )

    storage.save_human_ranking(ranking)
    return ranking


@router.get("/rankings/prompt/{prompt_name}")
def get_rankings(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get all human rankings for a prompt."""
    rankings = storage.get_human_rankings_by_prompt(prompt_name)
    return {
        "prompt_name": prompt_name,
        "num_rankings": len(rankings),
        "rankings": rankings
    }


@router.get("/recommendations/{prompt_name}")
def get_recommendation(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get recommendation for best config."""
    try:
        recommendation = calculate_recommendation(prompt_name, storage)
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/recommendations/weights/{prompt_name}")
def update_weights(
    prompt_name: str,
    quality_weight: float,
    speed_weight: float,
    cost_weight: float,
    updated_by: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Update ranking weights for a prompt."""
    weights = RankingWeights(
        prompt_name=prompt_name,
        quality_weight=quality_weight,
        speed_weight=speed_weight,
        cost_weight=cost_weight,
        updated_by=updated_by,
    )
    storage.save_weights(weights)

    # Recalculate recommendation with new weights
    recommendation = calculate_recommendation(prompt_name, storage, weights)

    return {
        "weights": weights,
        "updated_recommendation": recommendation
    }


@router.get("/compare/{prompt_name}")
def get_compare_data(
    prompt_name: str,
    run_id: Optional[str] = Query(None, description="Filter experiments by run_id"),
    storage: ResultStorage = Depends(get_storage),
):
    """Get all data needed for compare page (experiments, AI evals, rankings, recommendation)."""
    # Get experiments (filtered by run_id if provided)
    if run_id:
        experiments = storage.get_results_by_run(run_id)
        # Filter for successful only
        experiments = [exp for exp in experiments if exp.success]
    else:
        experiments = storage.get_results_by_prompt(prompt_name, success_only=True)

    if not experiments:
        raise HTTPException(status_code=404, detail=f"No experiments found for prompt: {prompt_name}")

    # Convert to dict format
    experiments_data = []
    for exp in experiments:
        experiments_data.append({
            "experiment_id": exp.experiment_id,
            "config_name": exp.config_name,
            "response": exp.response,
            "duration_seconds": exp.duration_seconds,
            "estimated_cost_usd": exp.estimated_cost_usd or 0.0,
            "total_tokens": exp.total_tokens or 0,
            "finish_reason": exp.finish_reason,
            "success": exp.success,
            "is_acceptable": exp.is_acceptable,
        })

    # Get AI evaluations - filter by experiments in this run
    experiment_ids = {exp.experiment_id for exp in experiments}
    all_ai_evaluations = storage.get_ai_evaluations_by_prompt(prompt_name)

    # Filter to only evaluations for experiments in the current view
    ai_evaluations = [e for e in all_ai_evaluations if e.experiment_id in experiment_ids]

    ai_evaluation_data = None
    if ai_evaluations:
        # Get the batch info from the first evaluation
        batch_id = ai_evaluations[0].batch_id
        batch = storage.get_ai_batch(batch_id)

        # Filter ranked_experiment_ids to only those in the current experiments
        filtered_ranked_ids = [eid for eid in batch.ranked_experiment_ids if eid in experiment_ids]

        ai_evaluation_data = {
            "batch_id": batch.batch_id,
            "model_evaluator": batch.model_evaluator,
            "review_prompt_id": batch.review_prompt_id,
            "ranked_experiment_ids": filtered_ranked_ids,
            "evaluations": [
                {
                    "experiment_id": e.experiment_id,
                    "ai_rank": e.ai_rank,
                    "overall_score": e.overall_score,
                    "criteria_scores": e.criteria_scores,
                    "justification": e.justification,
                    "strengths": e.strengths,
                    "weaknesses": e.weaknesses,
                }
                for e in ai_evaluations
            ]
        }

    # Get human rankings
    human_rankings = storage.get_human_rankings_by_prompt(prompt_name)
    human_rankings_data = [
        {
            "ranking_id": r.ranking_id,
            "evaluator_name": r.evaluator_name,
            "ranked_experiment_ids": r.ranked_experiment_ids,
            "ai_agreement_score": r.ai_agreement_score,
            "changes_from_ai": r.changes_from_ai,
            "created_at": r.created_at,
        }
        for r in human_rankings
    ]

    # Get recommendation
    recommendation_data = None
    try:
        recommendation = calculate_recommendation(prompt_name, storage)
        recommendation_data = {
            "recommended_config": recommendation.recommended_config,
            "final_score": recommendation.final_score,
            "quality_score": recommendation.quality_score,
            "speed_score": recommendation.speed_score,
            "cost_score": recommendation.cost_score,
            "confidence": recommendation.confidence,
            "confidence_factors": recommendation.confidence_factors,
            "reasoning": recommendation.reasoning,
            "runner_up_config": recommendation.runner_up_config,
            "score_difference": recommendation.score_difference,
        }
    except ValueError:
        # No recommendation available yet
        pass

    return {
        "prompt_name": prompt_name,
        "experiments": experiments_data,
        "ai_evaluation": ai_evaluation_data,
        "human_rankings": human_rankings_data,
        "recommendation": recommendation_data,
    }


# ============================================================================
# Prompt Management Routes
# ============================================================================


@router.get("/prompts/list")
def list_prompts(
    active_only: bool = Query(True),
    storage: ResultStorage = Depends(get_storage),
):
    """Get all prompts from database."""
    prompts = storage.get_all_prompts(active_only=active_only)
    return {
        "prompts": [
            {
                "name": p.name,
                "messages": p.messages,
                "description": p.description,
                "category": p.category,
                "tags": p.tags,
            }
            for p in prompts
        ]
    }


@router.get("/prompts/metadata")
def get_prompts_metadata(
    active_only: bool = Query(True),
    storage: ResultStorage = Depends(get_storage),
):
    """Get all prompts with metadata (status, recommended config, stats)."""
    prompts = storage.get_all_prompts(active_only=active_only)
    result = []

    for prompt in prompts:
        # Get experiments for this prompt
        experiments = storage.get_results_by_prompt(prompt.name)

        # Calculate metadata
        metadata = {
            "name": prompt.name,
            "status": "not_run",
            "recommended_config": None,
            "last_run_date": None,
            "total_cost": None,
            "num_configs": 0,
            "has_ai_evaluation": False,
            "has_user_ranking": False,
            "is_running": prompt.name in running_experiments,
        }

        if experiments:
            metadata["num_configs"] = len(experiments)
            metadata["status"] = "results_ready"

            # Get most recent run date
            latest_exp = max(experiments, key=lambda e: e.start_time)
            metadata["last_run_date"] = latest_exp.start_time.isoformat()

            # Calculate total cost of last run
            metadata["total_cost"] = sum(e.estimated_cost_usd or 0 for e in experiments)

            # Check for AI evaluation
            from prompt_benchmark.storage import DBAIEvaluationBatch
            from sqlalchemy.orm import Session as SQLSession
            from sqlalchemy import select

            with SQLSession(storage.engine) as session:
                stmt = select(DBAIEvaluationBatch).where(
                    DBAIEvaluationBatch.prompt_name == prompt.name
                ).order_by(DBAIEvaluationBatch.started_at.desc()).limit(1)
                ai_batch = session.execute(stmt).scalar_one_or_none()
                if ai_batch:
                    metadata["has_ai_evaluation"] = True
                    metadata["status"] = "ai_evaluated"

            # Check for human ranking and get recommended config
            rankings = storage.get_human_rankings_by_prompt(prompt.name)
            if rankings:
                metadata["has_user_ranking"] = True
                metadata["status"] = "user_ranked"

                # Get most recent ranking
                latest_ranking = max(rankings, key=lambda r: r.created_at)
                if latest_ranking.ranked_experiment_ids:
                    # First experiment in ranked list is the winner
                    winner_id = latest_ranking.ranked_experiment_ids[0]
                    winner_exp = next((e for e in experiments if e.experiment_id == winner_id), None)
                    if winner_exp:
                        metadata["recommended_config"] = winner_exp.config_name
            else:
                # If no human ranking, try to get recommendation from AI + weights
                try:
                    recommendation = calculate_recommendation(prompt.name, storage)
                    if recommendation and recommendation.recommended_config:
                        metadata["recommended_config"] = recommendation.recommended_config
                except:
                    pass

        result.append(metadata)

    return {"prompts": result}


@router.get("/prompts/detail/{prompt_name}")
def get_prompt_detail(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get a specific prompt by name."""
    prompt = storage.get_prompt(prompt_name)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")
    return {
        "name": prompt.name,
        "messages": prompt.messages,
        "description": prompt.description,
        "category": prompt.category,
        "tags": prompt.tags,
    }


@router.post("/prompts/create")
def create_prompt(
    name: str,
    messages: List[dict],
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: List[str] = [],
    storage: ResultStorage = Depends(get_storage),
):
    """Create a new prompt."""
    # Check if prompt already exists
    existing = storage.get_prompt(name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Prompt already exists: {name}")

    prompt = Prompt(
        name=name,
        messages=messages,
        description=description,
        category=category,
        tags=tags,
    )
    storage.save_prompt(prompt)
    return {"status": "created", "prompt": prompt}


@router.put("/prompts/update/{prompt_name}")
def update_prompt(
    prompt_name: str,
    messages: Optional[List[dict]] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    storage: ResultStorage = Depends(get_storage),
):
    """Update an existing prompt."""
    existing = storage.get_prompt(prompt_name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")

    # Update fields
    if messages is not None:
        existing.messages = messages
    if description is not None:
        existing.description = description
    if category is not None:
        existing.category = category
    if tags is not None:
        existing.tags = tags

    storage.save_prompt(existing)
    return {"status": "updated", "prompt": existing}


@router.delete("/prompts/delete/{prompt_name}")
def delete_prompt(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Delete a prompt (soft delete)."""
    success = storage.delete_prompt(prompt_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")
    return {"status": "deleted", "prompt_name": prompt_name}


@router.delete("/experiments/delete-by-prompt/{prompt_name}")
def delete_experiments_by_prompt(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Delete all experiment results and related data for a specific prompt."""
    from prompt_benchmark.storage import DBAIEvaluation, DBAIEvaluationBatch, DBHumanRanking

    logger.info(f"Deleting all experiments and related data for prompt: {prompt_name}")

    with SQLSession(storage.engine) as session:
        # Get experiment IDs for this prompt
        experiment_ids = [
            exp.experiment_id
            for exp in session.query(DBExperimentResult.experiment_id).filter(
                DBExperimentResult.prompt_name == prompt_name
            ).all()
        ]

        if not experiment_ids:
            logger.warning(f"No experiments found for prompt: {prompt_name}")
            return {
                "status": "no_experiments",
                "prompt_name": prompt_name,
                "deleted_experiments": 0,
                "deleted_evaluations": 0,
                "deleted_ai_evaluations": 0,
                "deleted_ai_batches": 0,
                "deleted_human_rankings": 0
            }

        logger.info(f"Found {len(experiment_ids)} experiments to delete")

        # Delete AI evaluations for these experiments
        ai_eval_count = session.query(DBAIEvaluation).filter(
            DBAIEvaluation.experiment_id.in_(experiment_ids)
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {ai_eval_count} AI evaluations")

        # Delete AI evaluation batches for this prompt
        ai_batch_count = session.query(DBAIEvaluationBatch).filter(
            DBAIEvaluationBatch.prompt_name == prompt_name
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {ai_batch_count} AI evaluation batches")

        # Delete human rankings for this prompt
        human_ranking_count = session.query(DBHumanRanking).filter(
            DBHumanRanking.prompt_name == prompt_name
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {human_ranking_count} human rankings")

        # Delete human evaluations
        eval_count = session.query(DBEvaluation).filter(
            DBEvaluation.experiment_id.in_(experiment_ids)
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {eval_count} human evaluations")

        # Delete experiments
        exp_count = session.query(DBExperimentResult).filter(
            DBExperimentResult.prompt_name == prompt_name
        ).delete(synchronize_session=False)
        logger.info(f"Deleted {exp_count} experiments")

        session.commit()
        logger.info(f"Successfully deleted all data for prompt: {prompt_name}")

    return {
        "status": "deleted",
        "prompt_name": prompt_name,
        "deleted_experiments": exp_count,
        "deleted_evaluations": eval_count,
        "deleted_ai_evaluations": ai_eval_count,
        "deleted_ai_batches": ai_batch_count,
        "deleted_human_rankings": human_ranking_count
    }


# ============================================================================
# LLM Config Management Routes
# ============================================================================


@router.get("/configs/list", response_model=List[LLMConfigResponse])
def list_configs(
    active_only: bool = Query(True),
    storage: ResultStorage = Depends(get_storage),
):
    """List all LLM configurations."""
    from prompt_benchmark.storage import DBLLMConfig, DBAIEvaluation
    from sqlalchemy.orm import Session as SQLSession

    logger.info(f"Listing configs (active_only={active_only})")

    with SQLSession(storage.engine) as session:
        from sqlalchemy import select
        stmt = select(DBLLMConfig)
        if active_only:
            stmt = stmt.where(DBLLMConfig.is_active == True)
        stmt = stmt.order_by(DBLLMConfig.created_at.desc())
        db_configs = session.execute(stmt).scalars().all()

        # Count unacceptable experiments and calculate averages for each config
        from sqlalchemy import func
        config_responses = []
        for c in db_configs:
            unacceptable_count = session.query(DBExperimentResult).filter(
                DBExperimentResult.config_name == c.name,
                DBExperimentResult.is_acceptable == False
            ).count()

            # Calculate average duration and cost for successful experiments
            stats = session.query(
                func.avg(DBExperimentResult.duration_seconds),
                func.avg(DBExperimentResult.estimated_cost_usd)
            ).filter(
                DBExperimentResult.config_name == c.name,
                DBExperimentResult.success == True
            ).first()

            avg_duration = float(stats[0]) if stats[0] is not None else None
            avg_cost = float(stats[1]) if stats[1] is not None else None

            # Calculate average AI score for this config
            ai_score_stats = session.query(
                func.avg(DBAIEvaluation.overall_score),
                func.count(DBAIEvaluation.evaluation_id)
            ).join(
                DBExperimentResult,
                DBAIEvaluation.experiment_id == DBExperimentResult.experiment_id
            ).filter(
                DBExperimentResult.config_name == c.name,
                DBExperimentResult.success == True
            ).first()

            # Defensive handling of AI score results
            if ai_score_stats and ai_score_stats[0] is not None:
                avg_ai_score = float(ai_score_stats[0])
                ai_eval_count = int(ai_score_stats[1]) if ai_score_stats[1] else 0
                logger.debug(f"Config {c.name}: AI score={avg_ai_score:.2f}, count={ai_eval_count}")
            else:
                avg_ai_score = None
                ai_eval_count = 0
                logger.debug(f"Config {c.name}: No AI evaluations found")

            config_responses.append(
                LLMConfigResponse(
                    name=c.name,
                    model=c.model,
                    max_output_tokens=c.max_output_tokens,
                    verbosity=c.verbosity,
                    reasoning_effort=c.reasoning_effort,
                    description=c.description,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    is_active=c.is_active,
                    unacceptable_count=unacceptable_count,
                    avg_duration_seconds=avg_duration,
                    avg_cost_usd=avg_cost,
                    avg_ai_score=avg_ai_score,
                    ai_evaluation_count=ai_eval_count
                )
            )

        return config_responses


@router.get("/configs/get/{name}", response_model=LLMConfigResponse)
def get_config(
    name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Get a specific LLM configuration by name."""
    from prompt_benchmark.storage import DBLLMConfig
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import select

    logger.info(f"Getting config: {name}")

    with SQLSession(storage.engine) as session:
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
        db_config = session.execute(stmt).scalar_one_or_none()

        if not db_config:
            raise HTTPException(status_code=404, detail=f"Config not found: {name}")

        return LLMConfigResponse(
            name=db_config.name,
            model=db_config.model,
            max_output_tokens=db_config.max_output_tokens,
            verbosity=db_config.verbosity,
            reasoning_effort=db_config.reasoning_effort,
            description=db_config.description,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            is_active=db_config.is_active
        )


@router.post("/configs/create", response_model=LLMConfigResponse)
def create_config(
    config_data: LLMConfigCreate,
    storage: ResultStorage = Depends(get_storage),
):
    """Create a new LLM configuration."""
    from prompt_benchmark.models import LangfuseConfig
    from prompt_benchmark.storage import DBLLMConfig
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import select

    logger.info(f"Creating config: {config_data.name}")

    # Check if config already exists
    with SQLSession(storage.engine) as session:
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == config_data.name)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail=f"Config already exists: {config_data.name}")

    # Create LangfuseConfig to validate
    langfuse_config = LangfuseConfig(
        model=config_data.model,
        max_output_tokens=config_data.max_output_tokens,
        verbosity=config_data.verbosity,
        reasoning_effort=config_data.reasoning_effort,
    )

    # Save to database
    storage.save_config(langfuse_config, config_data.name, config_data.description)

    # Return the created config
    with SQLSession(storage.engine) as session:
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == config_data.name)
        db_config = session.execute(stmt).scalar_one()

        return LLMConfigResponse(
            name=db_config.name,
            model=db_config.model,
            max_output_tokens=db_config.max_output_tokens,
            verbosity=db_config.verbosity,
            reasoning_effort=db_config.reasoning_effort,
            description=db_config.description,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            is_active=db_config.is_active
        )


@router.put("/configs/update/{name}", response_model=LLMConfigResponse)
def update_config(
    name: str,
    config_data: LLMConfigUpdate,
    storage: ResultStorage = Depends(get_storage),
):
    """Update an existing LLM configuration."""
    from prompt_benchmark.models import LangfuseConfig
    from prompt_benchmark.storage import DBLLMConfig
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import select

    logger.info(f"Updating config: {name}")

    # Get existing config
    with SQLSession(storage.engine) as session:
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
        db_config = session.execute(stmt).scalar_one_or_none()

        if not db_config:
            raise HTTPException(status_code=404, detail=f"Config not found: {name}")

        # Update fields if provided
        if config_data.model is not None:
            db_config.model = config_data.model
        if config_data.max_output_tokens is not None:
            db_config.max_output_tokens = config_data.max_output_tokens
        if config_data.verbosity is not None:
            db_config.verbosity = config_data.verbosity
        if config_data.reasoning_effort is not None:
            db_config.reasoning_effort = config_data.reasoning_effort
        if config_data.description is not None:
            db_config.description = config_data.description

        db_config.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(db_config)

        return LLMConfigResponse(
            name=db_config.name,
            model=db_config.model,
            max_output_tokens=db_config.max_output_tokens,
            verbosity=db_config.verbosity,
            reasoning_effort=db_config.reasoning_effort,
            description=db_config.description,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            is_active=db_config.is_active
        )


@router.delete("/configs/delete/{name}")
def delete_config(
    name: str,
    storage: ResultStorage = Depends(get_storage),
):
    """Delete an LLM configuration (soft delete)."""
    logger.info(f"Deleting config: {name}")

    success = storage.delete_config(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Config not found: {name}")

    return {"status": "deleted", "config_name": name}


@router.post("/configs/clone/{name}", response_model=LLMConfigResponse)
def clone_config(
    name: str,
    new_name: str = Query(...),
    storage: ResultStorage = Depends(get_storage),
):
    """Clone an existing LLM configuration with a new name."""
    from prompt_benchmark.storage import DBLLMConfig
    from sqlalchemy.orm import Session as SQLSession
    from sqlalchemy import select

    logger.info(f"Cloning config {name} to {new_name}")

    with SQLSession(storage.engine) as session:
        # Get source config
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
        source_config = session.execute(stmt).scalar_one_or_none()

        if not source_config:
            raise HTTPException(status_code=404, detail=f"Source config not found: {name}")

        # Check if new name already exists
        stmt = select(DBLLMConfig).where(DBLLMConfig.name == new_name)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail=f"Config already exists: {new_name}")

        # Create new config
        new_config = DBLLMConfig(
            name=new_name,
            model=source_config.model,
            max_output_tokens=source_config.max_output_tokens,
            verbosity=source_config.verbosity,
            reasoning_effort=source_config.reasoning_effort,
            description=f"Cloned from {name}" + (f": {source_config.description}" if source_config.description else ""),
            is_active=True
        )
        session.add(new_config)
        session.commit()
        session.refresh(new_config)

        return LLMConfigResponse(
            name=new_config.name,
            model=new_config.model,
            max_output_tokens=new_config.max_output_tokens,
            verbosity=new_config.verbosity,
            reasoning_effort=new_config.reasoning_effort,
            description=new_config.description,
            created_at=new_config.created_at,
            updated_at=new_config.updated_at,
            is_active=new_config.is_active
        )


# ============================================================================
# Run Experiments Routes
# ============================================================================


@router.post("/experiments/run-all-configs")
async def run_all_configs_for_prompt(
    prompt_name: str,
    background_tasks: BackgroundTasks,
    storage: ResultStorage = Depends(get_storage),
):
    """Run all configs for a specific prompt."""
    logger.info(f"Received request to run all configs for prompt: {prompt_name}")

    # Get the prompt
    prompt = storage.get_prompt(prompt_name)
    if not prompt:
        logger.error(f"Prompt not found: {prompt_name}")
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")

    logger.info(f"Found prompt: {prompt_name}")

    # Load all configs from database
    try:
        logger.info(f"Loading configs from database")
        configs = storage.get_all_configs_dict(active_only=True)
        logger.info(f"Loaded {len(configs)} configs from database: {list(configs.keys())}")

    except Exception as e:
        logger.error(f"Failed to load configs from database: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load configs: {str(e)}")

    if not configs:
        logger.error("No active configs found in database")
        raise HTTPException(status_code=404, detail="No active configs found")

    # Create a run record
    run_id = f"run_{uuid.uuid4().hex[:16]}"
    run = ExperimentRun(
        run_id=run_id,
        prompt_name=prompt_name,
        started_at=datetime.utcnow(),
        status="running",
        num_configs=len(configs),
        total_cost=0.0
    )
    storage.create_run(run)
    logger.info(f"Created run {run_id} for prompt: {prompt_name}")

    # Add to running experiments
    running_experiments.add(prompt_name)
    logger.info(f"Added '{prompt_name}' to running experiments. Current running: {running_experiments}")

    # Run experiments in background
    async def run_experiments():
        logger.info(f"Background task started for prompt: {prompt_name}, run_id: {run_id}")
        try:
            executor = ExperimentExecutor()
            logger.info(f"Executor created, starting batch run for {len(configs)} configs")

            # Pass storage and run_id to save results incrementally
            await executor.run_batch_async(prompt, configs, storage=storage, run_id=run_id)

            # Update run status to experiment_completed
            total_cost = sum(
                exp.estimated_cost_usd or 0.0
                for exp in storage.get_results_by_run(run_id)
            )
            storage.update_run_status(
                run_id,
                status="experiment_completed",
                completed_at=datetime.utcnow(),
                total_cost=total_cost
            )

            logger.info(f"Batch run completed successfully for prompt: {prompt_name}, run_id: {run_id}")
        except Exception as e:
            logger.error(f"Error in background task for prompt '{prompt_name}', run_id {run_id}: {str(e)}", exc_info=True)
            # Mark run as failed (we should add this status)
            storage.update_run_status(run_id, status="failed", completed_at=datetime.utcnow())
        finally:
            # Remove from running experiments when done
            running_experiments.discard(prompt_name)
            logger.info(f"Removed '{prompt_name}' from running experiments. Current running: {running_experiments}")

    # Add the async function directly to background tasks (don't use asyncio.run)
    background_tasks.add_task(run_experiments)

    logger.info(f"Background task scheduled for prompt: {prompt_name}, run_id: {run_id}")

    return {
        "status": "started",
        "prompt_name": prompt_name,
        "run_id": run_id,
        "num_configs": len(configs),
        "message": f"Running {len(configs)} configs for prompt '{prompt_name}' in background"
    }


# =============================================================================
# Experiment Run Management Endpoints
# =============================================================================

@router.get("/prompts/{prompt_name}/runs", response_model=List[ExperimentRunResponse])
def get_runs_for_prompt(
    prompt_name: str,
    storage: ResultStorage = Depends(get_storage)
):
    """Get all runs for a specific prompt."""
    logger.info(f"Getting runs for prompt: {prompt_name}")

    runs = storage.get_runs_by_prompt(prompt_name)

    # For each run, calculate recommended config based on rankings
    response_runs = []
    for run in runs:
        # Get experiments for this run
        experiments = storage.get_results_by_run(run.run_id)

        # Get human rankings for this prompt
        rankings = storage.get_human_rankings_by_prompt(prompt_name)

        # Find recommended config (best ranked in this run)
        recommended_config = None
        if rankings and experiments:
            # Get the most recent ranking
            latest_ranking = rankings[0]
            ranked_ids = latest_ranking.ranked_experiment_ids

            # Find the highest ranked experiment in this run
            experiment_ids_in_run = {exp.experiment_id for exp in experiments}
            for exp_id in ranked_ids:
                if exp_id in experiment_ids_in_run:
                    # Find the experiment and get its config name
                    exp = next((e for e in experiments if e.experiment_id == exp_id), None)
                    if exp:
                        recommended_config = exp.config_name
                        break
        elif experiments:
            # Fallback to AI evaluations if no human rankings
            # Query AI evaluations directly from database
            with SQLSession(storage.engine) as session:
                best_score = -1
                for exp in experiments:
                    # Get AI evaluation for this experiment
                    ai_eval = session.execute(text("""
                        SELECT overall_score FROM ai_evaluations
                        WHERE experiment_id = :exp_id
                        ORDER BY evaluated_at DESC
                        LIMIT 1
                    """), {"exp_id": exp.experiment_id}).first()

                    if ai_eval and ai_eval[0] > best_score:
                        best_score = ai_eval[0]
                        recommended_config = exp.config_name

        response_runs.append(ExperimentRunResponse(
            run_id=run.run_id,
            prompt_name=run.prompt_name,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=run.status,
            num_configs=run.num_configs,
            total_cost=run.total_cost,
            created_at=run.created_at,
            recommended_config=recommended_config
        ))

    return response_runs


@router.get("/runs/{run_id}", response_model=RunWithExperimentsResponse)
def get_run_details(
    run_id: str,
    storage: ResultStorage = Depends(get_storage)
):
    """Get details of a specific run with its experiments."""
    logger.info(f"Getting run details for: {run_id}")

    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    experiments = storage.get_results_by_run(run_id)

    # Convert to response models
    with SQLSession(storage.engine) as session:
        exp_responses = []
        for exp in experiments:
            # Get DB record for the experiment
            db_exp = session.query(DBExperimentResult).filter(
                DBExperimentResult.experiment_id == exp.experiment_id
            ).first()

            if db_exp:
                exp_responses.append(ExperimentResponse(
                    id=db_exp.id,
                    experiment_id=db_exp.experiment_id,
                    prompt_name=db_exp.prompt_name,
                    config_name=db_exp.config_name,
                    run_id=db_exp.run_id,
                    rendered_prompt=db_exp.rendered_prompt,
                    config_json=json.loads(db_exp.config_json),
                    response=db_exp.response,
                    finish_reason=db_exp.finish_reason,
                    start_time=db_exp.start_time,
                    end_time=db_exp.end_time,
                    duration_seconds=db_exp.duration_seconds,
                    prompt_tokens=db_exp.prompt_tokens or 0,
                    completion_tokens=db_exp.completion_tokens or 0,
                    total_tokens=db_exp.total_tokens or 0,
                    estimated_cost_usd=db_exp.estimated_cost_usd or 0.0,
                    error=db_exp.error,
                    success=db_exp.success,
                    is_acceptable=db_exp.is_acceptable,
                    metadata_json=json.loads(db_exp.metadata_json) if db_exp.metadata_json else {},
                    created_at=db_exp.created_at
                ))

    # Get recommended config
    rankings = storage.get_human_rankings_by_prompt(run.prompt_name)
    recommended_config = None
    if rankings and experiments:
        latest_ranking = rankings[0]
        ranked_ids = latest_ranking.ranked_experiment_ids
        experiment_ids_in_run = {exp.experiment_id for exp in experiments}
        for exp_id in ranked_ids:
            if exp_id in experiment_ids_in_run:
                exp = next((e for e in experiments if e.experiment_id == exp_id), None)
                if exp:
                    recommended_config = exp.config_name
                    break
    elif experiments:
        # Fallback to AI evaluations if no human rankings
        with SQLSession(storage.engine) as session:
            best_score = -1
            for exp in experiments:
                ai_eval = session.execute(text("""
                    SELECT overall_score FROM ai_evaluations
                    WHERE experiment_id = :exp_id
                    ORDER BY evaluated_at DESC
                    LIMIT 1
                """), {"exp_id": exp.experiment_id}).first()

                if ai_eval and ai_eval[0] > best_score:
                    best_score = ai_eval[0]
                    recommended_config = exp.config_name

    run_response = ExperimentRunResponse(
        run_id=run.run_id,
        prompt_name=run.prompt_name,
        started_at=run.started_at,
        completed_at=run.completed_at,
        status=run.status,
        num_configs=run.num_configs,
        total_cost=run.total_cost,
        created_at=run.created_at,
        recommended_config=recommended_config
    )

    return RunWithExperimentsResponse(
        run=run_response,
        experiments=exp_responses
    )


@router.delete("/runs/{run_id}")
def delete_run(
    run_id: str,
    storage: ResultStorage = Depends(get_storage)
):
    """Delete a specific run and all its experiments."""
    logger.info(f"Deleting run: {run_id}")

    success = storage.delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    logger.info(f"Successfully deleted run: {run_id}")
    return {"status": "deleted", "run_id": run_id}
