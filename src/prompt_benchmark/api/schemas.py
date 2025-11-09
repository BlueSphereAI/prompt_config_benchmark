"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ExperimentResponse(BaseModel):
    """Response model for experiment results."""
    id: int
    experiment_id: str
    prompt_name: str
    config_name: str
    rendered_prompt: str
    config_json: Dict[str, Any]
    response: str
    finish_reason: Optional[str]
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    error: Optional[str]
    success: bool
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    """Response model for evaluations."""
    id: int
    evaluation_id: str
    experiment_id: str
    result_id: int
    evaluation_type: str
    evaluator_name: str
    score: float
    criteria_json: Optional[Dict[str, Any]]
    notes: Optional[str]
    strengths: Optional[str]
    weaknesses: Optional[str]
    evaluated_at: datetime
    metadata_json: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class EvaluationCreate(BaseModel):
    """Request model for creating evaluations."""
    experiment_id: str
    evaluation_type: str = "human"
    evaluator_name: str
    score: float
    criteria: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConfigStats(BaseModel):
    """Statistics for a single config."""
    count: int
    success_rate: float
    avg_duration: Optional[float]
    min_duration: Optional[float]
    max_duration: Optional[float]
    avg_cost: Optional[float]
    total_cost: float
    avg_tokens: Optional[float]
    total_tokens: int
    avg_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]
    num_evaluations: int


class ConfigComparison(BaseModel):
    """Comparison of configs for a specific prompt."""
    prompt_name: str
    best_by_score: Optional[str]
    best_by_speed: Optional[str]
    best_by_cost: Optional[str]
    config_stats: Dict[str, ConfigStats]
    total_experiments: int
    total_evaluations: int


class OverallRankings(BaseModel):
    """Overall config rankings across all prompts."""
    config_stats: Dict[str, ConfigStats]
    total_experiments: int
    total_evaluations: int


class RunExperimentRequest(BaseModel):
    """Request model for running new experiments."""
    prompt_name: Optional[str] = None
    config_name: Optional[str] = None


class DashboardStats(BaseModel):
    """Dashboard summary statistics."""
    total_experiments: int
    total_prompts: int
    total_configs: int
    total_evaluations: int
    total_cost: float
    avg_duration: float
    success_rate: float
    recent_experiments: List[ExperimentResponse]
