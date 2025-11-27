"""
Storage layer for persisting experiments, results, and evaluations.

Uses SQLAlchemy with SQLite for database storage and JSON for exports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    create_engine, select
)
from sqlalchemy.orm import declarative_base, Session

from .models import (
    AIEvaluation,
    AIEvaluationBatch,
    ExperimentResult,
    ExperimentRun,
    Evaluation,
    HumanRanking,
    LangfuseConfig,
    MultiRunSession,
    Prompt,
    RankingWeights,
    Recommendation,
    ReviewPrompt,
)


Base = declarative_base()


class DBExperimentResult(Base):
    """Database model for experiment results."""

    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)
    config_name = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=True, index=True)  # Links experiments in the same run

    # Request details (JSON serialized)
    rendered_prompt = Column(Text, nullable=False)
    config_json = Column(Text, nullable=False)  # Serialized LangfuseConfig

    # Response
    response = Column(Text, nullable=False)
    finish_reason = Column(String, nullable=True)

    # Metrics
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)

    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Cost
    estimated_cost_usd = Column(Float, nullable=True)

    # Error handling
    error = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)

    # Acceptability flag
    is_acceptable = Column(Boolean, nullable=False, default=True)

    # Metadata (JSON serialized)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DBMultiRunSession(Base):
    """Database model for multi-run sessions."""

    __tablename__ = "multi_run_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)

    # Configuration
    num_runs = Column(Integer, nullable=False)
    runs_completed = Column(Integer, nullable=False, default=0)
    review_prompt_id = Column(String, nullable=False)

    # Status: running, completed, failed
    status = Column(String, nullable=False, index=True)

    # Timing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class DBExperimentRun(Base):
    """Database model for experiment runs."""

    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)

    # Multi-run session tracking
    session_id = Column(String, nullable=True, index=True)
    run_number = Column(Integer, nullable=False, default=1, index=True)

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Status: running, experiment_completed, analysis_completed
    status = Column(String, nullable=False)

    # Aggregates
    num_configs = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DBEvaluation(Base):
    """Database model for evaluations."""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String, unique=True, nullable=True, index=True)
    experiment_id = Column(String, nullable=False, index=True)
    result_id = Column(Integer, nullable=True)

    evaluation_type = Column(String, nullable=False)  # "human" or "ai"
    evaluator_name = Column(String, nullable=True)

    # Scoring
    score = Column(Float, nullable=False)
    criteria_json = Column(Text, nullable=True)  # Serialized dict

    # Feedback
    notes = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)

    # Metadata
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)


# ============================================================================
# AI-Assisted Ranking System Database Models
# ============================================================================


class DBReviewPrompt(Base):
    """Database model for review prompt templates."""

    __tablename__ = "review_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    criteria_json = Column(Text, nullable=False)  # JSON array
    default_model = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


class DBAIEvaluationBatch(Base):
    """Database model for AI evaluation batches."""

    __tablename__ = "ai_evaluation_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)
    review_prompt_id = Column(String, nullable=False)
    model_evaluator = Column(String, nullable=False)
    status = Column(String, nullable=False)
    num_experiments = Column(Integer, nullable=False)
    num_completed = Column(Integer, nullable=False, default=0)
    evaluation_ids_json = Column(Text, nullable=True)  # JSON array
    ranked_experiment_ids_json = Column(Text, nullable=True)  # JSON array
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_duration = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=False, default=0.0)


class DBAIEvaluation(Base):
    """Database model for AI evaluations."""

    __tablename__ = "ai_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String, unique=True, nullable=False, index=True)
    experiment_id = Column(String, nullable=False, index=True)
    review_prompt_id = Column(String, nullable=False)
    batch_id = Column(String, nullable=False, index=True)
    model_evaluator = Column(String, nullable=False)
    criteria_scores_json = Column(Text, nullable=False)  # JSON object
    overall_score = Column(Float, nullable=False)
    ai_rank = Column(Integer, nullable=False)
    justification = Column(Text, nullable=False)
    strengths_json = Column(Text, nullable=True)  # JSON array
    weaknesses_json = Column(Text, nullable=True)  # JSON array
    evaluated_at = Column(DateTime, nullable=False)
    evaluation_duration = Column(Float, nullable=False)


class DBHumanRanking(Base):
    """Database model for human rankings."""

    __tablename__ = "human_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ranking_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)
    evaluator_name = Column(String, nullable=False)
    ranked_experiment_ids_json = Column(Text, nullable=False)  # JSON array
    based_on_ai_batch_id = Column(String, nullable=True)
    changes_from_ai_json = Column(Text, nullable=True)  # JSON array
    ai_agreement_score = Column(Float, nullable=True)
    top_3_overlap = Column(Integer, nullable=True)
    exact_position_matches = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    time_spent_seconds = Column(Float, nullable=False)


class DBRankingWeights(Base):
    """Database model for ranking weights."""

    __tablename__ = "ranking_weights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String, unique=True, nullable=False, index=True)
    quality_weight = Column(Float, nullable=False, default=0.60)
    speed_weight = Column(Float, nullable=False, default=0.30)
    cost_weight = Column(Float, nullable=False, default=0.10)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class DBPrompt(Base):
    """Database model for prompts."""

    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    messages_json = Column(Text, nullable=False)  # JSON array of message objects
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    tags_json = Column(Text, nullable=True)  # JSON array of tags
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


class DBLLMConfig(Base):
    """Database model for LLM configurations."""

    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    model = Column(String, nullable=False)
    max_output_tokens = Column(Integer, nullable=True)
    verbosity = Column(String, nullable=True)  # "low", "medium", "high"
    reasoning_effort = Column(String, nullable=True)  # "minimal", "medium", "high"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


class ResultStorage:
    """
    Storage manager for experiment results and evaluations.

    Handles database operations and JSON exports.
    """

    def __init__(self, database_url: str = "sqlite:///data/results/benchmark.db"):
        """
        Initialize storage.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url

        # Create database directory if using SQLite file
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    def save_result(self, result: ExperimentResult) -> int:
        """
        Save an experiment result to the database.

        Args:
            result: The experiment result to save

        Returns:
            Database ID of the saved result
        """
        with Session(self.engine) as session:
            db_result = DBExperimentResult(
                experiment_id=result.experiment_id,
                prompt_name=result.prompt_name,
                config_name=result.config_name,
                run_id=result.run_id,
                rendered_prompt=result.rendered_prompt,
                config_json=result.config.model_dump_json(),
                response=result.response,
                finish_reason=result.finish_reason,
                start_time=result.start_time,
                end_time=result.end_time,
                duration_seconds=result.duration_seconds,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
                estimated_cost_usd=result.estimated_cost_usd,
                error=result.error,
                success=result.success,
                is_acceptable=result.is_acceptable,
                metadata_json=json.dumps(result.metadata) if result.metadata else None,
                created_at=result.created_at
            )
            session.add(db_result)
            session.commit()
            session.refresh(db_result)
            return db_result.id

    def get_result_by_experiment_id(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Retrieve a result by experiment ID.

        Args:
            experiment_id: The experiment ID

        Returns:
            ExperimentResult or None if not found
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.experiment_id == experiment_id
            )
            db_result = session.execute(stmt).scalar_one_or_none()

            if not db_result:
                return None

            return self._db_result_to_model(db_result)

    def get_results_by_prompt(
        self,
        prompt_name: str,
        success_only: bool = False
    ) -> List[ExperimentResult]:
        """
        Get all results for a specific prompt.

        Args:
            prompt_name: The prompt name
            success_only: If True, only return successful experiments

        Returns:
            List of ExperimentResults
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.prompt_name == prompt_name
            )
            if success_only:
                stmt = stmt.where(DBExperimentResult.success == True)
            db_results = session.execute(stmt).scalars().all()
            return [self._db_result_to_model(r) for r in db_results]

    def get_results_by_config(self, config_name: str) -> List[ExperimentResult]:
        """
        Get all results for a specific config.

        Args:
            config_name: The config name

        Returns:
            List of ExperimentResults
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.config_name == config_name
            )
            db_results = session.execute(stmt).scalars().all()
            return [self._db_result_to_model(r) for r in db_results]

    def get_all_results(self) -> List[ExperimentResult]:
        """
        Get all experiment results.

        Returns:
            List of all ExperimentResults
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult)
            db_results = session.execute(stmt).scalars().all()
            return [self._db_result_to_model(r) for r in db_results]

    def update_experiment_acceptability(self, experiment_id: str, is_acceptable: bool) -> bool:
        """
        Update the acceptability status of an experiment.

        Args:
            experiment_id: The experiment ID
            is_acceptable: Whether the result is acceptable

        Returns:
            True if updated successfully, False if experiment not found
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.experiment_id == experiment_id
            )
            db_result = session.execute(stmt).scalar_one_or_none()

            if not db_result:
                return False

            db_result.is_acceptable = is_acceptable
            session.commit()
            return True

    def save_evaluation(self, evaluation: Evaluation) -> int:
        """
        Save an evaluation to the database.

        Args:
            evaluation: The evaluation to save

        Returns:
            Database ID of the saved evaluation
        """
        with Session(self.engine) as session:
            db_eval = DBEvaluation(
                evaluation_id=evaluation.id,
                experiment_id=evaluation.experiment_id,
                result_id=evaluation.result_id,
                evaluation_type=evaluation.evaluation_type,
                evaluator_name=evaluation.evaluator_name,
                score=evaluation.score,
                criteria_json=json.dumps(evaluation.criteria) if evaluation.criteria else None,
                notes=evaluation.notes,
                strengths=evaluation.strengths,
                weaknesses=evaluation.weaknesses,
                evaluated_at=evaluation.evaluated_at,
                metadata_json=json.dumps(evaluation.metadata) if evaluation.metadata else None
            )
            session.add(db_eval)
            session.commit()
            session.refresh(db_eval)
            return db_eval.id

    def get_evaluations_by_experiment(self, experiment_id: str) -> List[Evaluation]:
        """
        Get all evaluations for an experiment.

        Args:
            experiment_id: The experiment ID

        Returns:
            List of Evaluations
        """
        with Session(self.engine) as session:
            stmt = select(DBEvaluation).where(
                DBEvaluation.experiment_id == experiment_id
            )
            db_evals = session.execute(stmt).scalars().all()
            return [self._db_eval_to_model(e) for e in db_evals]

    def get_all_evaluations(self) -> List[Evaluation]:
        """
        Get all evaluations.

        Returns:
            List of all Evaluations
        """
        with Session(self.engine) as session:
            stmt = select(DBEvaluation)
            db_evals = session.execute(stmt).scalars().all()
            return [self._db_eval_to_model(e) for e in db_evals]

    def export_results_to_json(self, output_path: Union[str, Path]) -> None:
        """
        Export all results to a JSON file.

        Args:
            output_path: Path to the output JSON file
        """
        results = self.get_all_results()
        data = [r.model_dump(mode='json') for r in results]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def export_evaluations_to_json(self, output_path: Union[str, Path]) -> None:
        """
        Export all evaluations to a JSON file.

        Args:
            output_path: Path to the output JSON file
        """
        evaluations = self.get_all_evaluations()
        data = [e.model_dump(mode='json') for e in evaluations]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _db_result_to_model(self, db_result: DBExperimentResult) -> ExperimentResult:
        """Convert database model to Pydantic model."""
        return ExperimentResult(
            experiment_id=db_result.experiment_id,
            prompt_name=db_result.prompt_name,
            config_name=db_result.config_name,
            run_id=db_result.run_id,
            rendered_prompt=db_result.rendered_prompt,
            config=LangfuseConfig.model_validate_json(db_result.config_json),
            response=db_result.response,
            finish_reason=db_result.finish_reason,
            start_time=db_result.start_time,
            end_time=db_result.end_time,
            duration_seconds=db_result.duration_seconds,
            prompt_tokens=db_result.prompt_tokens,
            completion_tokens=db_result.completion_tokens,
            total_tokens=db_result.total_tokens,
            estimated_cost_usd=db_result.estimated_cost_usd,
            error=db_result.error,
            success=db_result.success,
            is_acceptable=db_result.is_acceptable,
            metadata=json.loads(db_result.metadata_json) if db_result.metadata_json else {},
            created_at=db_result.created_at
        )

    def _db_eval_to_model(self, db_eval: DBEvaluation) -> Evaluation:
        """Convert database evaluation to Pydantic model."""
        return Evaluation(
            id=db_eval.evaluation_id,
            experiment_id=db_eval.experiment_id,
            result_id=db_eval.result_id,
            evaluation_type=db_eval.evaluation_type,
            evaluator_name=db_eval.evaluator_name,
            score=db_eval.score,
            criteria=json.loads(db_eval.criteria_json) if db_eval.criteria_json else {},
            notes=db_eval.notes,
            strengths=db_eval.strengths,
            weaknesses=db_eval.weaknesses,
            evaluated_at=db_eval.evaluated_at,
            metadata=json.loads(db_eval.metadata_json) if db_eval.metadata_json else {}
        )

    # ========================================================================
    # AI-Assisted Ranking System Storage Methods
    # ========================================================================

    # Review Prompts
    def save_review_prompt(self, review_prompt: ReviewPrompt) -> int:
        """Save a review prompt template."""
        with Session(self.engine) as session:
            db_prompt = DBReviewPrompt(
                prompt_id=review_prompt.prompt_id,
                name=review_prompt.name,
                description=review_prompt.description,
                template=review_prompt.template,
                system_prompt=review_prompt.system_prompt,
                criteria_json=json.dumps(review_prompt.criteria),
                default_model=review_prompt.default_model,
                created_by=review_prompt.created_by,
                created_at=review_prompt.created_at,
                updated_at=review_prompt.updated_at,
                is_active=review_prompt.is_active
            )
            session.add(db_prompt)
            session.commit()
            session.refresh(db_prompt)
            return db_prompt.id

    def get_review_prompt(self, prompt_id: str) -> Optional[ReviewPrompt]:
        """Get a review prompt by ID."""
        with Session(self.engine) as session:
            stmt = select(DBReviewPrompt).where(DBReviewPrompt.prompt_id == prompt_id)
            db_prompt = session.execute(stmt).scalar_one_or_none()
            if not db_prompt:
                return None
            return ReviewPrompt(
                prompt_id=db_prompt.prompt_id,
                name=db_prompt.name,
                description=db_prompt.description,
                template=db_prompt.template,
                system_prompt=db_prompt.system_prompt,
                criteria=json.loads(db_prompt.criteria_json),
                default_model=db_prompt.default_model,
                created_by=db_prompt.created_by,
                created_at=db_prompt.created_at,
                updated_at=db_prompt.updated_at,
                is_active=db_prompt.is_active
            )

    def get_all_review_prompts(self, active_only: bool = False) -> List[ReviewPrompt]:
        """Get all review prompts."""
        with Session(self.engine) as session:
            stmt = select(DBReviewPrompt)
            if active_only:
                stmt = stmt.where(DBReviewPrompt.is_active == True)
            db_prompts = session.execute(stmt).scalars().all()
            return [
                ReviewPrompt(
                    prompt_id=p.prompt_id,
                    name=p.name,
                    description=p.description,
                    template=p.template,
                    system_prompt=p.system_prompt,
                    criteria=json.loads(p.criteria_json),
                    default_model=p.default_model,
                    created_by=p.created_by,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    is_active=p.is_active
                )
                for p in db_prompts
            ]

    # AI Evaluation Batches
    def save_ai_batch(self, batch: AIEvaluationBatch) -> int:
        """Save an AI evaluation batch."""
        with Session(self.engine) as session:
            db_batch = DBAIEvaluationBatch(
                batch_id=batch.batch_id,
                prompt_name=batch.prompt_name,
                review_prompt_id=batch.review_prompt_id,
                model_evaluator=batch.model_evaluator,
                status=batch.status,
                num_experiments=batch.num_experiments,
                num_completed=batch.num_completed,
                evaluation_ids_json=json.dumps(batch.evaluation_ids),
                ranked_experiment_ids_json=json.dumps(batch.ranked_experiment_ids),
                started_at=batch.started_at,
                completed_at=batch.completed_at,
                total_duration=batch.total_duration,
                estimated_cost=batch.estimated_cost
            )
            session.add(db_batch)
            session.commit()
            session.refresh(db_batch)
            return db_batch.id

    def update_ai_batch(self, batch: AIEvaluationBatch) -> None:
        """Update an AI evaluation batch."""
        with Session(self.engine) as session:
            stmt = select(DBAIEvaluationBatch).where(DBAIEvaluationBatch.batch_id == batch.batch_id)
            db_batch = session.execute(stmt).scalar_one()
            db_batch.status = batch.status
            db_batch.num_completed = batch.num_completed
            db_batch.evaluation_ids_json = json.dumps(batch.evaluation_ids)
            db_batch.ranked_experiment_ids_json = json.dumps(batch.ranked_experiment_ids)
            db_batch.completed_at = batch.completed_at
            db_batch.total_duration = batch.total_duration
            db_batch.estimated_cost = batch.estimated_cost
            session.commit()

    def get_ai_batch(self, batch_id: str) -> Optional[AIEvaluationBatch]:
        """Get an AI evaluation batch."""
        with Session(self.engine) as session:
            stmt = select(DBAIEvaluationBatch).where(DBAIEvaluationBatch.batch_id == batch_id)
            db_batch = session.execute(stmt).scalar_one_or_none()
            if not db_batch:
                return None
            return AIEvaluationBatch(
                batch_id=db_batch.batch_id,
                prompt_name=db_batch.prompt_name,
                review_prompt_id=db_batch.review_prompt_id,
                model_evaluator=db_batch.model_evaluator,
                status=db_batch.status,
                num_experiments=db_batch.num_experiments,
                num_completed=db_batch.num_completed,
                evaluation_ids=json.loads(db_batch.evaluation_ids_json or "[]"),
                ranked_experiment_ids=json.loads(db_batch.ranked_experiment_ids_json or "[]"),
                started_at=db_batch.started_at,
                completed_at=db_batch.completed_at,
                total_duration=db_batch.total_duration,
                estimated_cost=db_batch.estimated_cost
            )

    # AI Evaluations
    def save_ai_evaluation(self, evaluation: AIEvaluation) -> int:
        """Save an AI evaluation."""
        with Session(self.engine) as session:
            db_eval = DBAIEvaluation(
                evaluation_id=evaluation.evaluation_id,
                experiment_id=evaluation.experiment_id,
                review_prompt_id=evaluation.review_prompt_id,
                batch_id=evaluation.batch_id,
                model_evaluator=evaluation.model_evaluator,
                criteria_scores_json=json.dumps(evaluation.criteria_scores),
                overall_score=evaluation.overall_score,
                ai_rank=evaluation.ai_rank,
                justification=evaluation.justification,
                strengths_json=json.dumps(evaluation.strengths),
                weaknesses_json=json.dumps(evaluation.weaknesses),
                evaluated_at=evaluation.evaluated_at,
                evaluation_duration=evaluation.evaluation_duration
            )
            session.add(db_eval)
            session.commit()
            session.refresh(db_eval)
            return db_eval.id

    def get_ai_evaluations_by_prompt(self, prompt_name: str) -> List[AIEvaluation]:
        """Get all AI evaluations for a prompt."""
        with Session(self.engine) as session:
            # Get batches for this prompt
            batch_stmt = select(DBAIEvaluationBatch).where(
                DBAIEvaluationBatch.prompt_name == prompt_name
            ).order_by(DBAIEvaluationBatch.started_at.desc())
            batches = session.execute(batch_stmt).scalars().all()

            if not batches:
                return []

            # Get evaluations from ALL batches for this prompt (not just latest)
            # This ensures evaluations are available across all runs
            batch_ids = [b.batch_id for b in batches]
            eval_stmt = select(DBAIEvaluation).where(
                DBAIEvaluation.batch_id.in_(batch_ids)
            )
            db_evals = session.execute(eval_stmt).scalars().all()

            return [
                AIEvaluation(
                    evaluation_id=e.evaluation_id,
                    experiment_id=e.experiment_id,
                    review_prompt_id=e.review_prompt_id,
                    batch_id=e.batch_id,
                    model_evaluator=e.model_evaluator,
                    criteria_scores=json.loads(e.criteria_scores_json),
                    overall_score=e.overall_score,
                    ai_rank=e.ai_rank,
                    justification=e.justification,
                    strengths=json.loads(e.strengths_json or "[]"),
                    weaknesses=json.loads(e.weaknesses_json or "[]"),
                    evaluated_at=e.evaluated_at,
                    evaluation_duration=e.evaluation_duration
                )
                for e in db_evals
            ]

    # Human Rankings
    def save_human_ranking(self, ranking: HumanRanking) -> int:
        """Save a human ranking."""
        with Session(self.engine) as session:
            db_ranking = DBHumanRanking(
                ranking_id=ranking.ranking_id,
                prompt_name=ranking.prompt_name,
                evaluator_name=ranking.evaluator_name,
                ranked_experiment_ids_json=json.dumps(ranking.ranked_experiment_ids),
                based_on_ai_batch_id=ranking.based_on_ai_batch_id,
                changes_from_ai_json=json.dumps(ranking.changes_from_ai),
                ai_agreement_score=ranking.ai_agreement_score,
                top_3_overlap=ranking.top_3_overlap,
                exact_position_matches=ranking.exact_position_matches,
                notes=ranking.notes,
                created_at=ranking.created_at,
                time_spent_seconds=ranking.time_spent_seconds
            )
            session.add(db_ranking)
            session.commit()
            session.refresh(db_ranking)
            return db_ranking.id

    def get_human_rankings_by_prompt(self, prompt_name: str) -> List[HumanRanking]:
        """Get all human rankings for a prompt."""
        with Session(self.engine) as session:
            stmt = select(DBHumanRanking).where(
                DBHumanRanking.prompt_name == prompt_name
            )
            db_rankings = session.execute(stmt).scalars().all()
            return [
                HumanRanking(
                    ranking_id=r.ranking_id,
                    prompt_name=r.prompt_name,
                    evaluator_name=r.evaluator_name,
                    ranked_experiment_ids=json.loads(r.ranked_experiment_ids_json),
                    based_on_ai_batch_id=r.based_on_ai_batch_id,
                    changes_from_ai=json.loads(r.changes_from_ai_json or "[]"),
                    ai_agreement_score=r.ai_agreement_score,
                    top_3_overlap=r.top_3_overlap,
                    exact_position_matches=r.exact_position_matches,
                    notes=r.notes,
                    created_at=r.created_at,
                    time_spent_seconds=r.time_spent_seconds
                )
                for r in db_rankings
            ]

    # Ranking Weights
    def save_weights(self, weights: RankingWeights) -> int:
        """Save or update ranking weights."""
        with Session(self.engine) as session:
            # Check if weights exist for this prompt
            stmt = select(DBRankingWeights).where(
                DBRankingWeights.prompt_name == weights.prompt_name
            )
            db_weights = session.execute(stmt).scalar_one_or_none()

            if db_weights:
                # Update existing
                db_weights.quality_weight = weights.quality_weight
                db_weights.speed_weight = weights.speed_weight
                db_weights.cost_weight = weights.cost_weight
                db_weights.updated_by = weights.updated_by
                db_weights.updated_at = weights.updated_at
            else:
                # Create new
                db_weights = DBRankingWeights(
                    prompt_name=weights.prompt_name,
                    quality_weight=weights.quality_weight,
                    speed_weight=weights.speed_weight,
                    cost_weight=weights.cost_weight,
                    updated_by=weights.updated_by,
                    updated_at=weights.updated_at
                )
                session.add(db_weights)

            session.commit()
            session.refresh(db_weights)
            return db_weights.id

    def get_weights(self, prompt_name: str) -> Optional[RankingWeights]:
        """Get ranking weights for a prompt."""
        with Session(self.engine) as session:
            stmt = select(DBRankingWeights).where(
                DBRankingWeights.prompt_name == prompt_name
            )
            db_weights = session.execute(stmt).scalar_one_or_none()
            if not db_weights:
                return None
            return RankingWeights(
                prompt_name=db_weights.prompt_name,
                quality_weight=db_weights.quality_weight,
                speed_weight=db_weights.speed_weight,
                cost_weight=db_weights.cost_weight,
                updated_by=db_weights.updated_by,
                updated_at=db_weights.updated_at
            )

    # Prompts
    def save_prompt(self, prompt: Prompt) -> int:
        """Save a new prompt or update existing one."""
        with Session(self.engine) as session:
            # Check if prompt exists
            stmt = select(DBPrompt).where(DBPrompt.name == prompt.name)
            db_prompt = session.execute(stmt).scalar_one_or_none()

            if db_prompt:
                # Update existing
                db_prompt.messages_json = json.dumps(prompt.messages)
                db_prompt.description = prompt.description
                db_prompt.category = prompt.category
                db_prompt.tags_json = json.dumps(prompt.tags)
                db_prompt.updated_at = datetime.utcnow()
            else:
                # Create new
                db_prompt = DBPrompt(
                    name=prompt.name,
                    messages_json=json.dumps(prompt.messages),
                    description=prompt.description,
                    category=prompt.category,
                    tags_json=json.dumps(prompt.tags),
                    is_active=True
                )
                session.add(db_prompt)

            session.commit()
            session.refresh(db_prompt)
            return db_prompt.id

    def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        with Session(self.engine) as session:
            stmt = select(DBPrompt).where(DBPrompt.name == name)
            db_prompt = session.execute(stmt).scalar_one_or_none()
            if not db_prompt:
                return None
            return Prompt(
                name=db_prompt.name,
                messages=json.loads(db_prompt.messages_json),
                description=db_prompt.description,
                category=db_prompt.category,
                tags=json.loads(db_prompt.tags_json or "[]")
            )

    def get_all_prompts(self, active_only: bool = True) -> List[Prompt]:
        """Get all prompts."""
        with Session(self.engine) as session:
            stmt = select(DBPrompt)
            if active_only:
                stmt = stmt.where(DBPrompt.is_active == True)
            stmt = stmt.order_by(DBPrompt.created_at.desc())
            db_prompts = session.execute(stmt).scalars().all()
            return [
                Prompt(
                    name=p.name,
                    messages=json.loads(p.messages_json),
                    description=p.description,
                    category=p.category,
                    tags=json.loads(p.tags_json or "[]")
                )
                for p in db_prompts
            ]

    def delete_prompt(self, name: str) -> bool:
        """Delete a prompt (soft delete by marking inactive)."""
        with Session(self.engine) as session:
            stmt = select(DBPrompt).where(DBPrompt.name == name)
            db_prompt = session.execute(stmt).scalar_one_or_none()
            if not db_prompt:
                return False
            db_prompt.is_active = False
            db_prompt.updated_at = datetime.utcnow()
            session.commit()
            return True

    # LLM Config Management
    def get_all_configs_dict(self, active_only: bool = True) -> Dict[str, LangfuseConfig]:
        """
        Get all LLM configurations as a dict mapping name to LangfuseConfig.

        Args:
            active_only: If True, only return active configs

        Returns:
            Dict mapping config name to LangfuseConfig object
        """
        with Session(self.engine) as session:
            stmt = select(DBLLMConfig)
            if active_only:
                stmt = stmt.where(DBLLMConfig.is_active == True)
            stmt = stmt.order_by(DBLLMConfig.created_at.desc())
            db_configs = session.execute(stmt).scalars().all()

            return {
                db_config.name: self._db_config_to_langfuse(db_config)
                for db_config in db_configs
            }

    def get_all_configs(self, active_only: bool = True) -> List[LangfuseConfig]:
        """
        Get all LLM configurations from database.

        Args:
            active_only: If True, only return active configs

        Returns:
            List of LangfuseConfig objects
        """
        with Session(self.engine) as session:
            stmt = select(DBLLMConfig)
            if active_only:
                stmt = stmt.where(DBLLMConfig.is_active == True)
            stmt = stmt.order_by(DBLLMConfig.created_at.desc())
            db_configs = session.execute(stmt).scalars().all()
            return [self._db_config_to_langfuse(c) for c in db_configs]

    def get_config(self, name: str) -> Optional[LangfuseConfig]:
        """
        Get a single LLM configuration by name.

        Args:
            name: The config name

        Returns:
            LangfuseConfig or None if not found
        """
        with Session(self.engine) as session:
            stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
            db_config = session.execute(stmt).scalar_one_or_none()
            if not db_config:
                return None
            return self._db_config_to_langfuse(db_config)

    def save_config(self, config: LangfuseConfig, name: str, description: Optional[str] = None) -> int:
        """
        Save or update an LLM configuration.

        Args:
            config: The LangfuseConfig to save
            name: The config name (unique identifier)
            description: Optional description of the config

        Returns:
            Database ID of the saved config
        """
        with Session(self.engine) as session:
            stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
            db_config = session.execute(stmt).scalar_one_or_none()

            if db_config:
                # Update existing
                db_config.model = config.model
                db_config.max_output_tokens = config.max_output_tokens
                db_config.verbosity = config.verbosity
                db_config.reasoning_effort = config.reasoning_effort
                db_config.description = description
                db_config.updated_at = datetime.utcnow()
            else:
                # Create new
                db_config = DBLLMConfig(
                    name=name,
                    model=config.model,
                    max_output_tokens=config.max_output_tokens,
                    verbosity=config.verbosity,
                    reasoning_effort=config.reasoning_effort,
                    description=description,
                    is_active=True
                )
                session.add(db_config)

            session.commit()
            session.refresh(db_config)
            return db_config.id

    def delete_config(self, name: str) -> bool:
        """
        Delete an LLM configuration (soft delete by marking inactive).

        Args:
            name: The config name

        Returns:
            True if config was deleted, False if not found
        """
        with Session(self.engine) as session:
            stmt = select(DBLLMConfig).where(DBLLMConfig.name == name)
            db_config = session.execute(stmt).scalar_one_or_none()
            if not db_config:
                return False
            db_config.is_active = False
            db_config.updated_at = datetime.utcnow()
            session.commit()
            return True

    def _db_config_to_langfuse(self, db_config: DBLLMConfig) -> LangfuseConfig:
        """
        Convert a database config model to LangfuseConfig.

        Args:
            db_config: The database model

        Returns:
            LangfuseConfig instance
        """
        config_dict = {
            "model": db_config.model,
        }
        if db_config.max_output_tokens is not None:
            config_dict["max_output_tokens"] = db_config.max_output_tokens
        if db_config.verbosity is not None:
            config_dict["verbosity"] = db_config.verbosity
        if db_config.reasoning_effort is not None:
            config_dict["reasoning_effort"] = db_config.reasoning_effort

        return LangfuseConfig(**config_dict)

    # ========================================================================
    # Experiment Run Management
    # ========================================================================

    def create_run(self, run: ExperimentRun) -> int:
        """
        Create a new experiment run record.

        Args:
            run: The ExperimentRun to create

        Returns:
            Database ID of the created run
        """
        with Session(self.engine) as session:
            db_run = DBExperimentRun(
                run_id=run.run_id,
                prompt_name=run.prompt_name,
                session_id=run.session_id,
                run_number=run.run_number,
                started_at=run.started_at,
                completed_at=run.completed_at,
                status=run.status,
                num_configs=run.num_configs,
                total_cost=run.total_cost,
                created_at=run.created_at
            )
            session.add(db_run)
            session.commit()
            session.refresh(db_run)
            return db_run.id

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        """
        Get a run by its ID.

        Args:
            run_id: The run ID

        Returns:
            ExperimentRun or None if not found
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentRun).where(DBExperimentRun.run_id == run_id)
            db_run = session.execute(stmt).scalar_one_or_none()
            if not db_run:
                return None
            return self._db_run_to_model(db_run)

    def get_runs_by_prompt(self, prompt_name: str) -> List[ExperimentRun]:
        """
        Get all runs for a specific prompt.

        Args:
            prompt_name: The prompt name

        Returns:
            List of ExperimentRuns, ordered by most recent first
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentRun).where(
                DBExperimentRun.prompt_name == prompt_name
            ).order_by(DBExperimentRun.started_at.desc())
            db_runs = session.execute(stmt).scalars().all()
            return [self._db_run_to_model(r) for r in db_runs]

    def update_run_status(
        self,
        run_id: str,
        status: str,
        completed_at: Optional[datetime] = None,
        total_cost: Optional[float] = None
    ) -> bool:
        """
        Update a run's status and optionally its completion time and cost.

        Args:
            run_id: The run ID
            status: New status (running, experiment_completed, analysis_completed)
            completed_at: Optional completion timestamp
            total_cost: Optional total cost

        Returns:
            True if updated successfully, False if run not found
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentRun).where(DBExperimentRun.run_id == run_id)
            db_run = session.execute(stmt).scalar_one_or_none()

            if not db_run:
                return False

            db_run.status = status
            if completed_at is not None:
                db_run.completed_at = completed_at
            if total_cost is not None:
                db_run.total_cost = total_cost

            session.commit()
            return True

    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run and all its associated experiments and evaluations.

        Args:
            run_id: The run ID

        Returns:
            True if deleted successfully, False if run not found
        """
        with Session(self.engine) as session:
            # Get the run first to check if it exists
            stmt = select(DBExperimentRun).where(DBExperimentRun.run_id == run_id)
            db_run = session.execute(stmt).scalar_one_or_none()

            if not db_run:
                return False

            # Get all experiment IDs for this run
            exp_stmt = select(DBExperimentResult).where(
                DBExperimentResult.run_id == run_id
            )
            experiments = session.execute(exp_stmt).scalars().all()
            experiment_ids = [exp.experiment_id for exp in experiments]

            # Delete AI evaluations for these experiments
            if experiment_ids:
                for exp_id in experiment_ids:
                    session.execute(
                        DBAIEvaluation.__table__.delete().where(
                            DBAIEvaluation.experiment_id == exp_id
                        )
                    )

            # Delete experiments for this run
            session.execute(
                DBExperimentResult.__table__.delete().where(
                    DBExperimentResult.run_id == run_id
                )
            )

            # Delete the run itself
            session.execute(
                DBExperimentRun.__table__.delete().where(
                    DBExperimentRun.run_id == run_id
                )
            )

            session.commit()
            return True

    def get_results_by_run(self, run_id: str) -> List[ExperimentResult]:
        """
        Get all experiment results for a specific run.

        Args:
            run_id: The run ID

        Returns:
            List of ExperimentResults
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.run_id == run_id
            )
            db_results = session.execute(stmt).scalars().all()
            return [self._db_result_to_model(r) for r in db_results]

    def _db_run_to_model(self, db_run: DBExperimentRun) -> ExperimentRun:
        """Convert database run model to Pydantic model."""
        return ExperimentRun(
            run_id=db_run.run_id,
            prompt_name=db_run.prompt_name,
            session_id=db_run.session_id,
            run_number=db_run.run_number,
            started_at=db_run.started_at,
            completed_at=db_run.completed_at,
            status=db_run.status,
            num_configs=db_run.num_configs,
            total_cost=db_run.total_cost,
            created_at=db_run.created_at
        )

    def _db_multi_run_session_to_model(self, db_session: DBMultiRunSession) -> MultiRunSession:
        """Convert database multi-run session model to Pydantic model."""
        return MultiRunSession(
            session_id=db_session.session_id,
            prompt_name=db_session.prompt_name,
            num_runs=db_session.num_runs,
            runs_completed=db_session.runs_completed,
            review_prompt_id=db_session.review_prompt_id,
            status=db_session.status,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            completed_at=db_session.completed_at
        )

    # ========================================================================
    # Multi-Run Session Management
    # ========================================================================

    def create_multi_run_session(self, session: MultiRunSession) -> int:
        """
        Create a new multi-run session record.

        Args:
            session: The MultiRunSession to create

        Returns:
            Database ID of the created session
        """
        with Session(self.engine) as db_session:
            db_multi_run = DBMultiRunSession(
                session_id=session.session_id,
                prompt_name=session.prompt_name,
                num_runs=session.num_runs,
                runs_completed=session.runs_completed,
                review_prompt_id=session.review_prompt_id,
                status=session.status,
                created_at=session.created_at,
                updated_at=session.updated_at,
                completed_at=session.completed_at
            )
            db_session.add(db_multi_run)
            db_session.commit()
            db_session.refresh(db_multi_run)
            return db_multi_run.id

    def get_multi_run_session(self, session_id: str) -> Optional[MultiRunSession]:
        """
        Get a multi-run session by its ID.

        Args:
            session_id: The session ID

        Returns:
            MultiRunSession or None if not found
        """
        with Session(self.engine) as session:
            stmt = select(DBMultiRunSession).where(DBMultiRunSession.session_id == session_id)
            db_session = session.execute(stmt).scalar_one_or_none()
            if not db_session:
                return None
            return self._db_multi_run_session_to_model(db_session)

    def get_multi_run_sessions_by_prompt(self, prompt_name: str) -> List[MultiRunSession]:
        """
        Get all multi-run sessions for a specific prompt.

        Args:
            prompt_name: The prompt name

        Returns:
            List of MultiRunSessions, ordered by most recent first
        """
        with Session(self.engine) as session:
            stmt = select(DBMultiRunSession).where(
                DBMultiRunSession.prompt_name == prompt_name
            ).order_by(DBMultiRunSession.created_at.desc())
            db_sessions = session.execute(stmt).scalars().all()
            return [self._db_multi_run_session_to_model(s) for s in db_sessions]

    def update_multi_run_session(
        self,
        session_id: str,
        runs_completed: Optional[int] = None,
        status: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update a multi-run session's progress and status.

        Args:
            session_id: The session ID
            runs_completed: Number of runs completed
            status: New status (running, completed, failed)
            completed_at: Optional completion timestamp

        Returns:
            True if updated successfully, False if session not found
        """
        with Session(self.engine) as session:
            stmt = select(DBMultiRunSession).where(DBMultiRunSession.session_id == session_id)
            db_multi_run = session.execute(stmt).scalar_one_or_none()

            if not db_multi_run:
                return False

            if runs_completed is not None:
                db_multi_run.runs_completed = runs_completed
            if status is not None:
                db_multi_run.status = status
            if completed_at is not None:
                db_multi_run.completed_at = completed_at

            db_multi_run.updated_at = datetime.utcnow()

            session.commit()
            return True

    def get_runs_by_session(self, session_id: str) -> List[ExperimentRun]:
        """
        Get all runs for a specific multi-run session.

        Args:
            session_id: The session ID

        Returns:
            List of ExperimentRuns, ordered by run_number
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentRun).where(
                DBExperimentRun.session_id == session_id
            ).order_by(DBExperimentRun.run_number.asc())
            db_runs = session.execute(stmt).scalars().all()
            return [self._db_run_to_model(r) for r in db_runs]
