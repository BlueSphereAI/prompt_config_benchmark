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
    LOW = "low"
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
    run_id: Optional[str] = Field(None, description="ID of the run this experiment belongs to")

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

    # Acceptability
    is_acceptable: bool = Field(True, description="Whether this result is acceptable")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MultiRunSession(BaseModel):
    """
    A multi-run session that executes multiple sequential runs with AI ranking.

    Each session contains multiple runs that are executed sequentially,
    with AI ranking performed after each run completes.
    """
    session_id: str = Field(..., description="Unique session identifier")
    prompt_name: str = Field(..., description="Name of the prompt for all runs")

    # Configuration
    num_runs: int = Field(..., ge=1, description="Total number of runs to execute")
    runs_completed: int = Field(default=0, description="Number of runs completed so far")
    review_prompt_id: str = Field(..., description="Review prompt template for AI ranking")

    # Status: running, completed, failed
    status: str = Field(..., description="Current status of the session")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When the session completed")


class ExperimentRun(BaseModel):
    """
    A single run of experiments for a prompt.

    Groups all experiments executed together when "Run All Configs" is clicked.
    Can be part of a multi-run session or standalone.
    """
    run_id: str = Field(..., description="Unique run identifier")
    prompt_name: str = Field(..., description="Name of the prompt this run is for")

    # Multi-run session tracking
    session_id: Optional[str] = Field(None, description="Session ID if part of multi-run")
    run_number: int = Field(default=1, description="Run number within session (1, 2, 3...)")

    # Timing
    started_at: datetime = Field(..., description="When the run started")
    completed_at: Optional[datetime] = Field(None, description="When the run completed")

    # Status: running, experiment_completed, analysis_completed
    status: str = Field(..., description="Current status of the run")

    # Aggregates
    num_configs: int = Field(..., description="Number of configs tested in this run")
    total_cost: Optional[float] = Field(None, description="Total cost of all experiments in this run")

    # Metadata
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


# ============================================================================
# AI-Assisted Ranking System Models
# ============================================================================


class ReviewPrompt(BaseModel):
    """Template for AI evaluation prompts."""
    prompt_id: str = Field(..., description="UUID")
    name: str = Field(..., description="e.g., 'Code Quality Reviewer'")
    description: Optional[str] = None

    # The actual prompt template
    template: str = Field(..., description="Uses {original_prompt}, {config_name}, {result}")
    system_prompt: Optional[str] = None

    # Evaluation criteria
    criteria: List[str] = Field(..., description="e.g., ['accuracy', 'clarity', 'completeness']")

    # Default evaluator model
    default_model: str = Field(..., description="e.g., 'gpt-4-turbo', 'claude-3-opus'")

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class AIEvaluation(BaseModel):
    """Result of AI evaluating a single experiment."""
    evaluation_id: str = Field(..., description="UUID")
    experiment_id: str = Field(..., description="Links to experiment")
    review_prompt_id: str = Field(..., description="Which template was used")
    batch_id: str = Field(..., description="Groups evaluations from same batch")

    # Evaluator info
    model_evaluator: str = Field(..., description="e.g., 'gpt-4-turbo', 'claude-3-opus'")

    # Scores
    criteria_scores: Dict[str, float] = Field(..., description="e.g., {'accuracy': 8.5, 'clarity': 9.0}")
    overall_score: float = Field(..., ge=0, le=10, description="0-10")

    # Ranking within this batch
    ai_rank: int = Field(..., ge=1, description="1 = best, 2 = second, etc.")

    # Explanations
    justification: str = Field(..., description="2-3 sentence explanation")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses identified")

    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_duration: float = Field(..., ge=0, description="Seconds taken")


class AIEvaluationBatch(BaseModel):
    """Tracks a batch AI evaluation of all configs for a prompt."""
    batch_id: str = Field(..., description="UUID")
    prompt_name: str
    review_prompt_id: str
    model_evaluator: str

    # Status
    status: str = Field(..., description="pending, running, completed, failed")
    num_experiments: int
    num_completed: int = 0

    # Results
    evaluation_ids: List[str] = Field(default_factory=list, description="All evaluations in this batch")
    ranked_experiment_ids: List[str] = Field(default_factory=list, description="Ordered by AI ranking")

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration: Optional[float] = None

    # Cost
    estimated_cost: float = 0.0


class HumanRanking(BaseModel):
    """Human's ranking of configs for a prompt."""
    ranking_id: str = Field(..., description="UUID")
    prompt_name: str
    evaluator_name: str = Field(..., description="Who did the ranking")

    # The ranking (ordered list, best to worst)
    ranked_experiment_ids: List[str]

    # Context
    based_on_ai_batch_id: Optional[str] = Field(None, description="If started from AI ranking")

    # Track changes from AI
    changes_from_ai: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="e.g., [{'experiment_id': 'x', 'from_rank': 2, 'to_rank': 1}]"
    )

    # Agreement metrics
    ai_agreement_score: Optional[float] = Field(None, ge=-1, le=1, description="Kendall Tau: -1 to 1")
    top_3_overlap: Optional[int] = Field(None, ge=0, le=3, description="How many of top 3 match")
    exact_position_matches: Optional[int] = Field(None, ge=0, description="How many same position")

    # User notes
    notes: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_seconds: float = Field(..., ge=0, description="How long they spent ranking")


class RankingWeights(BaseModel):
    """Configurable weights for recommendation algorithm."""
    prompt_name: str = Field(..., description="Weights can be per-prompt or global ('_default')")
    quality_weight: float = Field(0.60, ge=0, le=1)
    speed_weight: float = Field(0.30, ge=0, le=1)
    cost_weight: float = Field(0.10, ge=0, le=1)

    # Metadata
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('cost_weight')
    @classmethod
    def validate_weights_sum(cls, v, info):
        """Validate that weights sum to 1.0."""
        quality = info.data.get('quality_weight', 0)
        speed = info.data.get('speed_weight', 0)
        total = quality + speed + v
        if abs(total - 1.0) > 0.001:  # Allow small floating point error
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class Recommendation(BaseModel):
    """Best config recommendation for a prompt."""
    prompt_name: str
    recommended_config: str = Field(..., description="Config name")

    # Scoring
    final_score: float = Field(..., ge=0, le=10, description="Weighted score")
    quality_score: float = Field(..., ge=0, le=10)
    speed_score: float = Field(..., ge=0, le=10)
    cost_score: float = Field(..., ge=0, le=10)

    # Confidence
    confidence: str = Field(..., description="HIGH, MEDIUM, or LOW")
    confidence_factors: List[str] = Field(default_factory=list, description="Reasons for confidence level")

    # Evidence
    num_ai_evaluations: int = Field(default=0, ge=0)
    num_human_rankings: int = Field(default=0, ge=0)
    consensus_agreement: Optional[float] = Field(None, description="If multiple humans")

    # Reasoning
    reasoning: str = Field(..., description="Human-readable explanation")

    # Alternatives
    runner_up_config: Optional[str] = None
    score_difference: Optional[float] = Field(None, ge=0, description="How close was runner-up")

    generated_at: datetime = Field(default_factory=datetime.utcnow)
