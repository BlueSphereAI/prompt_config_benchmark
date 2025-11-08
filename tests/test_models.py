"""Tests for data models."""

import pytest
from datetime import datetime

from prompt_benchmark.models import (
    LangfuseConfig,
    Prompt,
    Experiment,
    ExperimentResult,
    Evaluation,
    EvaluationType,
    VerbosityLevel,
    ReasoningEffort,
)


class TestLangfuseConfig:
    """Test LangfuseConfig model."""

    def test_basic_config(self):
        """Test creating a basic config."""
        config = LangfuseConfig(
            model="gpt-4",
            temperature=0.7,
            max_output_tokens=1500
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_output_tokens == 1500

    def test_gpt5_config(self):
        """Test GPT-5 config with verbosity and reasoning."""
        config = LangfuseConfig(
            model="gpt-5",
            max_output_tokens=2000,
            verbosity=VerbosityLevel.HIGH,
            reasoning_effort=ReasoningEffort.HIGH
        )
        assert config.model == "gpt-5"
        assert config.verbosity == "high"
        assert config.reasoning_effort == "high"
        assert config.temperature is None  # GPT-5 doesn't use temperature

    def test_temperature_validation(self):
        """Test temperature range validation."""
        with pytest.raises(ValueError):
            LangfuseConfig(
                model="gpt-4",
                temperature=3.0  # Out of range
            )

    def test_optional_parameters(self):
        """Test configs with optional parameters."""
        config = LangfuseConfig(
            model="gpt-3.5-turbo",
            temperature=0.5,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.5
        assert config.presence_penalty == 0.5


class TestPrompt:
    """Test Prompt model."""

    def test_basic_prompt(self):
        """Test creating a basic prompt."""
        prompt = Prompt(
            name="test-prompt",
            template="Hello, {name}!",
            description="A greeting prompt"
        )
        assert prompt.name == "test-prompt"
        assert prompt.template == "Hello, {name}!"

    def test_prompt_rendering(self):
        """Test rendering prompts with variables."""
        prompt = Prompt(
            name="greeting",
            template="Hello, {name}! You are {age} years old.",
            variables={"name": "Alice", "age": 30}
        )

        # Render with defaults
        result = prompt.render()
        assert result == "Hello, Alice! You are 30 years old."

        # Override variables
        result = prompt.render(name="Bob", age=25)
        assert result == "Hello, Bob! You are 25 years old."

    def test_prompt_with_tags(self):
        """Test prompt with tags and categories."""
        prompt = Prompt(
            name="test",
            template="Test",
            category="testing",
            tags=["test", "example"]
        )
        assert prompt.category == "testing"
        assert len(prompt.tags) == 2
        assert "test" in prompt.tags


class TestExperimentResult:
    """Test ExperimentResult model."""

    def test_successful_result(self):
        """Test creating a successful result."""
        config = LangfuseConfig(model="gpt-4", temperature=0.7)
        start = datetime.utcnow()
        end = datetime.utcnow()

        result = ExperimentResult(
            experiment_id="test-123",
            prompt_name="test-prompt",
            config_name="test-config",
            rendered_prompt="What is 2+2?",
            config=config,
            response="4",
            start_time=start,
            end_time=end,
            duration_seconds=1.5,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=0.0001,
            success=True
        )

        assert result.success is True
        assert result.response == "4"
        assert result.duration_seconds == 1.5
        assert result.total_tokens == 15

    def test_failed_result(self):
        """Test creating a failed result with error."""
        config = LangfuseConfig(model="gpt-4")
        start = datetime.utcnow()
        end = datetime.utcnow()

        result = ExperimentResult(
            experiment_id="test-456",
            prompt_name="test-prompt",
            config_name="test-config",
            rendered_prompt="Test",
            config=config,
            response="",
            start_time=start,
            end_time=end,
            duration_seconds=0.1,
            error="API Error",
            success=False
        )

        assert result.success is False
        assert result.error == "API Error"
        assert result.response == ""


class TestEvaluation:
    """Test Evaluation model."""

    def test_human_evaluation(self):
        """Test creating a human evaluation."""
        evaluation = Evaluation(
            experiment_id="test-123",
            evaluation_type=EvaluationType.HUMAN,
            evaluator_name="John Doe",
            score=8.5,
            criteria={"accuracy": 9.0, "clarity": 8.0},
            notes="Good response",
            strengths="Clear and concise",
            weaknesses="Could be more detailed"
        )

        assert evaluation.evaluation_type == "human"
        assert evaluation.score == 8.5
        assert evaluation.criteria["accuracy"] == 9.0

    def test_ai_evaluation(self):
        """Test creating an AI evaluation."""
        evaluation = Evaluation(
            experiment_id="test-456",
            evaluation_type=EvaluationType.AI,
            evaluator_name="gpt-4",
            score=7.5,
            notes="Automated evaluation"
        )

        assert evaluation.evaluation_type == "ai"
        assert evaluation.evaluator_name == "gpt-4"

    def test_score_validation(self):
        """Test score range validation."""
        with pytest.raises(ValueError):
            Evaluation(
                experiment_id="test",
                evaluation_type=EvaluationType.HUMAN,
                score=11.0  # Out of range
            )
