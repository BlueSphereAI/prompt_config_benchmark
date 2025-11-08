"""Tests for storage layer."""

import pytest
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path

from prompt_benchmark.models import (
    LangfuseConfig,
    ExperimentResult,
    Evaluation,
    EvaluationType,
)
from prompt_benchmark.storage import ResultStorage


class TestResultStorage:
    """Test ResultStorage functionality."""

    @pytest.fixture
    def storage(self):
        """Create a temporary storage instance."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield ResultStorage(f"sqlite:///{db_path}")

    @pytest.fixture
    def sample_result(self):
        """Create a sample experiment result."""
        config = LangfuseConfig(model="gpt-4", temperature=0.7)
        return ExperimentResult(
            experiment_id="test-123",
            prompt_name="test-prompt",
            config_name="test-config",
            rendered_prompt="What is 2+2?",
            config=config,
            response="4",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=1.5,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=0.0001,
            success=True
        )

    @pytest.fixture
    def sample_evaluation(self):
        """Create a sample evaluation."""
        return Evaluation(
            experiment_id="test-123",
            evaluation_type=EvaluationType.HUMAN,
            evaluator_name="tester",
            score=8.5,
            criteria={"accuracy": 9.0},
            notes="Good response"
        )

    def test_save_and_retrieve_result(self, storage, sample_result):
        """Test saving and retrieving a result."""
        # Save result
        result_id = storage.save_result(sample_result)
        assert result_id > 0

        # Retrieve by experiment ID
        retrieved = storage.get_result_by_experiment_id(sample_result.experiment_id)
        assert retrieved is not None
        assert retrieved.experiment_id == sample_result.experiment_id
        assert retrieved.response == sample_result.response
        assert retrieved.config.model == sample_result.config.model

    def test_get_results_by_prompt(self, storage, sample_result):
        """Test retrieving results by prompt name."""
        # Save multiple results for same prompt
        storage.save_result(sample_result)

        # Create another result with same prompt
        result2 = ExperimentResult(
            experiment_id="test-456",
            prompt_name="test-prompt",
            config_name="other-config",
            rendered_prompt="Test",
            config=LangfuseConfig(model="gpt-3.5-turbo"),
            response="Response",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=1.0,
            success=True
        )
        storage.save_result(result2)

        # Retrieve by prompt
        results = storage.get_results_by_prompt("test-prompt")
        assert len(results) == 2

    def test_get_results_by_config(self, storage, sample_result):
        """Test retrieving results by config name."""
        storage.save_result(sample_result)

        results = storage.get_results_by_config("test-config")
        assert len(results) == 1
        assert results[0].config_name == "test-config"

    def test_save_and_retrieve_evaluation(self, storage, sample_result, sample_evaluation):
        """Test saving and retrieving evaluations."""
        # Save result first
        storage.save_result(sample_result)

        # Save evaluation
        eval_id = storage.save_evaluation(sample_evaluation)
        assert eval_id > 0

        # Retrieve evaluations for experiment
        evals = storage.get_evaluations_by_experiment(sample_result.experiment_id)
        assert len(evals) == 1
        assert evals[0].score == 8.5
        assert evals[0].evaluation_type == "human"

    def test_get_all_results(self, storage, sample_result):
        """Test getting all results."""
        storage.save_result(sample_result)

        all_results = storage.get_all_results()
        assert len(all_results) >= 1

    def test_get_all_evaluations(self, storage, sample_evaluation):
        """Test getting all evaluations."""
        storage.save_evaluation(sample_evaluation)

        all_evals = storage.get_all_evaluations()
        assert len(all_evals) >= 1

    def test_export_results_to_json(self, storage, sample_result):
        """Test exporting results to JSON."""
        storage.save_result(sample_result)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            storage.export_results_to_json(output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_evaluations_to_json(self, storage, sample_evaluation):
        """Test exporting evaluations to JSON."""
        storage.save_evaluation(sample_evaluation)

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "evaluations.json"
            storage.export_evaluations_to_json(output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0
