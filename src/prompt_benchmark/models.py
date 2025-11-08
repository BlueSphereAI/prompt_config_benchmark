"""
Data models for the prompt configuration benchmark framework.

These models define the structure for configurations, prompts, experiments,
results, and evaluations following the Langfuse configuration format.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class VerbosityLevel(str, Enum):
    """GPT-5 text verbosity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReasoningEffort(str, Enum):
    """GPT-5 reasoning effort levels."""
    MINIMAL = "minimal"
    MEDIUM = "medium"
    HIGH = "high"


class ModelTier(str, Enum):
    """Model performance tiers."""
    FAST = "fast"
    SMART = "smart"
    REASONING = "reasoning"


class LangfuseConfig(BaseModel):
    """
    Langfuse configuration format for LLM parameters.

    This follows the tier configuration system with support for OpenAI-specific
    parameters like verbosity and reasoning_effort.
    """
    model: str = Field(..., description="Model identifier (e.g., gpt-4, gpt-3.5-turbo)")
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0). Not supported by GPT-5."
    )
    max_output_tokens: Optional[int] = Field(
        None,
        gt=0,
        description="Maximum tokens in response"
    )
    verbosity: Optional[VerbosityLevel] = Field(
        None,
        description="GPT-5 text verbosity level"
    )
    reasoning_effort: Optional[ReasoningEffort] = Field(
        None,
        description="GPT-5 reasoning effort level"
    )

    # Additional optional parameters
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)

    model_config = {"use_enum_values": True}

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v, info):
        """Warn if temperature is set for GPT-5 models."""
        if v is not None and info.data.get('model', '').startswith('gpt-5'):
            # GPT-5 doesn't support temperature, but we'll store it
            pass
        return v


class Prompt(BaseModel):
    """
    A prompt definition with metadata.

    Supports OpenAI messages format (list of message dicts with role and content).
    """
    name: str = Field(..., description="Unique identifier for the prompt")
    messages: List[Dict[str, str]] = Field(
        ...,
        description="List of message objects with 'role' and 'content' keys"
    )
    description: Optional[str] = Field(None, description="Human-readable description")
    category: Optional[str] = Field(None, description="Category or type of prompt")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get the messages for the prompt.

        Returns:
            List of message dictionaries with role and content
        """
        return self.messages

    def to_string(self) -> str:
        """
        Convert messages to a single string for display/storage.

        Returns:
            Concatenated string of all message content
        """
        return "\n\n".join(
            f"[{msg['role']}]\n{msg['content']}" for msg in self.messages
        )


class Experiment(BaseModel):
    """
    Definition of a single experiment run.

    Combines a prompt with a specific configuration to test.
    """
    id: Optional[str] = Field(None, description="Unique experiment ID (auto-generated)")
    prompt_name: str = Field(..., description="Name of the prompt to use")
    config: LangfuseConfig = Field(..., description="LLM configuration to test")
    config_name: str = Field(..., description="Human-readable name for this config")
    prompt_variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables to fill in the prompt"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
    """
    Results from running an experiment.

    Includes the LLM response, timing data, token usage, and cost estimates.
    """
    experiment_id: str = Field(..., description="ID of the experiment")
    prompt_name: str = Field(..., description="Name of the prompt used")
    config_name: str = Field(..., description="Name of the configuration used")

    # Request details
    rendered_prompt: str = Field(..., description="The actual prompt sent to the LLM")
    config: LangfuseConfig = Field(..., description="Configuration used")

    # Response
    response: str = Field(..., description="LLM response text")
    finish_reason: Optional[str] = Field(None, description="Why the completion finished")

    # Metrics
    start_time: datetime = Field(..., description="When the request started")
    end_time: datetime = Field(..., description="When the request completed")
    duration_seconds: float = Field(..., ge=0, description="Total time in seconds")

    # Token usage
    prompt_tokens: Optional[int] = Field(None, ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)

    # Cost (estimated based on model pricing)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)

    # Error handling
    error: Optional[str] = Field(None, description="Error message if request failed")
    success: bool = Field(..., description="Whether the request succeeded")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationType(str, Enum):
    """Type of evaluation."""
    HUMAN = "human"
    AI = "ai"


class Evaluation(BaseModel):
    """
    Evaluation/scoring of an experiment result.

    Can be done by humans or AI evaluators.
    """
    id: Optional[str] = Field(None, description="Unique evaluation ID")
    experiment_id: str = Field(..., description="ID of the experiment being evaluated")
    result_id: Optional[str] = Field(None, description="Database ID of the result")

    evaluation_type: EvaluationType = Field(..., description="Human or AI evaluation")
    evaluator_name: Optional[str] = Field(
        None,
        description="Name of evaluator (person or model)"
    )

    # Scoring
    score: float = Field(..., ge=0, le=10, description="Score from 0-10")
    criteria: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown by criteria (e.g., accuracy, relevance, coherence)"
    )

    # Feedback
    notes: Optional[str] = Field(None, description="Evaluator's notes or explanation")
    strengths: Optional[str] = Field(None, description="What was good")
    weaknesses: Optional[str] = Field(None, description="What could be better")

    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}


class BenchmarkRun(BaseModel):
    """
    A collection of experiments run together as a benchmark suite.

    Groups multiple experiments for comparison and analysis.
    """
    id: Optional[str] = Field(None, description="Unique run ID")
    name: str = Field(..., description="Name of this benchmark run")
    description: Optional[str] = Field(None, description="Description of the benchmark")

    prompts: List[str] = Field(..., description="List of prompt names to test")
    configs: List[Dict[str, LangfuseConfig]] = Field(
        ...,
        description="List of {config_name: LangfuseConfig} to test"
    )

    # Execution tracking
    status: str = Field(default="pending", description="pending, running, completed, failed")
    total_experiments: int = Field(default=0, ge=0)
    completed_experiments: int = Field(default=0, ge=0)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfigComparison(BaseModel):
    """
    Comparison results for different configurations on a specific prompt.
    """
    prompt_name: str = Field(..., description="Prompt being compared")

    # Rankings
    best_by_score: Optional[str] = Field(None, description="Config with highest avg score")
    best_by_speed: Optional[str] = Field(None, description="Config with lowest avg time")
    best_by_cost: Optional[str] = Field(None, description="Config with lowest avg cost")

    # Statistics by config
    config_stats: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Statistics for each config (avg_score, avg_time, avg_cost, etc.)"
    )

    # Overall metrics
    total_experiments: int = Field(default=0, ge=0)
    total_evaluations: int = Field(default=0, ge=0)

    generated_at: datetime = Field(default_factory=datetime.utcnow)
