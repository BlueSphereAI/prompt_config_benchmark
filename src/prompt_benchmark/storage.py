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
    ExperimentResult,
    Evaluation,
    LangfuseConfig,
)


Base = declarative_base()


class DBExperimentResult(Base):
    """Database model for experiment results."""

    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, unique=True, nullable=False, index=True)
    prompt_name = Column(String, nullable=False, index=True)
    config_name = Column(String, nullable=False, index=True)

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

    # Metadata (JSON serialized)
    metadata_json = Column(Text, nullable=True)
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

    def get_results_by_prompt(self, prompt_name: str) -> List[ExperimentResult]:
        """
        Get all results for a specific prompt.

        Args:
            prompt_name: The prompt name

        Returns:
            List of ExperimentResults
        """
        with Session(self.engine) as session:
            stmt = select(DBExperimentResult).where(
                DBExperimentResult.prompt_name == prompt_name
            )
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
