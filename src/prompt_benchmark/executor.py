"""
Experiment executor for running LLM prompts with timing and metrics collection.

Handles OpenAI API calls, measures performance, and captures results.
"""

import os
import time
import uuid
from datetime import datetime
from typing import Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from .models import (
    Experiment,
    ExperimentResult,
    LangfuseConfig,
    Prompt,
)


# Pricing per 1M tokens (as of early 2024, update as needed)
MODEL_PRICING = {
    "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    # GPT-5 pricing (placeholder, adjust when available)
    "gpt-5": {"input": 15.0, "output": 45.0},
    "gpt-5-mini": {"input": 2.0, "output": 6.0},
}


class ExperimentExecutor:
    """
    Execute experiments and collect results.

    Handles OpenAI API calls with proper timing, error handling,
    and metrics collection.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the executor.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=self.api_key)

    def run_experiment(
        self,
        prompt: Prompt,
        config: LangfuseConfig,
        config_name: str,
        prompt_variables: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> ExperimentResult:
        """
        Run a single experiment.

        Args:
            prompt: The prompt to use
            config: The LLM configuration
            config_name: Human-readable name for this config
            prompt_variables: Variables to fill in the prompt template
            metadata: Additional metadata to store

        Returns:
            ExperimentResult with timing and metrics
        """
        # Generate experiment ID
        experiment_id = str(uuid.uuid4())

        # Render the prompt
        prompt_variables = prompt_variables or {}
        try:
            rendered_prompt = prompt.render(**prompt_variables)
        except KeyError as e:
            return ExperimentResult(
                experiment_id=experiment_id,
                prompt_name=prompt.name,
                config_name=config_name,
                rendered_prompt="",
                config=config,
                response="",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=0.0,
                error=f"Failed to render prompt: {e}",
                success=False,
                metadata=metadata or {}
            )

        # Prepare API call parameters
        api_params = self._prepare_api_params(config, rendered_prompt)

        # Execute with timing
        start_time = datetime.utcnow()
        start_perf = time.perf_counter()

        try:
            completion = self.client.chat.completions.create(**api_params)
            end_perf = time.perf_counter()
            end_time = datetime.utcnow()

            # Extract response and metrics
            result = self._extract_result(
                experiment_id=experiment_id,
                prompt_name=prompt.name,
                config_name=config_name,
                rendered_prompt=rendered_prompt,
                config=config,
                completion=completion,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end_perf - start_perf,
                metadata=metadata or {}
            )

        except Exception as e:
            end_perf = time.perf_counter()
            end_time = datetime.utcnow()

            result = ExperimentResult(
                experiment_id=experiment_id,
                prompt_name=prompt.name,
                config_name=config_name,
                rendered_prompt=rendered_prompt,
                config=config,
                response="",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end_perf - start_perf,
                error=str(e),
                success=False,
                metadata=metadata or {}
            )

        return result

    def _prepare_api_params(self, config: LangfuseConfig, prompt_text: str) -> Dict:
        """
        Prepare OpenAI API parameters from Langfuse config.

        Args:
            config: Langfuse configuration
            prompt_text: The rendered prompt

        Returns:
            Dictionary of API parameters
        """
        params = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt_text}],
        }

        # Add optional parameters if present
        if config.temperature is not None and not config.model.startswith("gpt-5"):
            params["temperature"] = config.temperature

        if config.max_output_tokens is not None:
            params["max_tokens"] = config.max_output_tokens

        if config.top_p is not None:
            params["top_p"] = config.top_p

        if config.frequency_penalty is not None:
            params["frequency_penalty"] = config.frequency_penalty

        if config.presence_penalty is not None:
            params["presence_penalty"] = config.presence_penalty

        # GPT-5 specific parameters (if supported in future API)
        # Currently these would go in model config or be handled differently
        # Keeping them in the config for tracking purposes

        return params

    def _extract_result(
        self,
        experiment_id: str,
        prompt_name: str,
        config_name: str,
        rendered_prompt: str,
        config: LangfuseConfig,
        completion: ChatCompletion,
        start_time: datetime,
        end_time: datetime,
        duration_seconds: float,
        metadata: Dict
    ) -> ExperimentResult:
        """
        Extract result data from OpenAI completion.

        Args:
            experiment_id: Experiment ID
            prompt_name: Prompt name
            config_name: Config name
            rendered_prompt: The rendered prompt text
            config: Configuration used
            completion: OpenAI completion response
            start_time: Request start time
            end_time: Request end time
            duration_seconds: Duration in seconds
            metadata: Additional metadata

        Returns:
            ExperimentResult with all metrics
        """
        # Extract response text
        response_text = ""
        finish_reason = None
        if completion.choices:
            choice = completion.choices[0]
            if choice.message and choice.message.content:
                response_text = choice.message.content
            finish_reason = choice.finish_reason

        # Extract token usage
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else None
        completion_tokens = usage.completion_tokens if usage else None
        total_tokens = usage.total_tokens if usage else None

        # Estimate cost
        estimated_cost = self._estimate_cost(
            config.model,
            prompt_tokens,
            completion_tokens
        )

        return ExperimentResult(
            experiment_id=experiment_id,
            prompt_name=prompt_name,
            config_name=config_name,
            rendered_prompt=rendered_prompt,
            config=config,
            response=response_text,
            finish_reason=finish_reason,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            success=True,
            metadata=metadata
        )

    def _estimate_cost(
        self,
        model: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int]
    ) -> Optional[float]:
        """
        Estimate the cost of an API call.

        Args:
            model: Model identifier
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD, or None if pricing unknown
        """
        if prompt_tokens is None or completion_tokens is None:
            return None

        # Find matching pricing (handle model variants)
        pricing = None
        for model_prefix, model_pricing in MODEL_PRICING.items():
            if model.startswith(model_prefix):
                pricing = model_pricing
                break

        if not pricing:
            return None

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def run_batch(
        self,
        prompt: Prompt,
        configs: Dict[str, LangfuseConfig],
        prompt_variables: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, ExperimentResult]:
        """
        Run multiple experiments with different configs on the same prompt.

        Args:
            prompt: The prompt to use
            configs: Dictionary mapping config names to LangfuseConfig instances
            prompt_variables: Variables for the prompt
            metadata: Additional metadata

        Returns:
            Dictionary mapping config names to results
        """
        results = {}
        for config_name, config in configs.items():
            result = self.run_experiment(
                prompt=prompt,
                config=config,
                config_name=config_name,
                prompt_variables=prompt_variables,
                metadata=metadata
            )
            results[config_name] = result

        return results

    def run_full_benchmark(
        self,
        prompts: Dict[str, Prompt],
        configs: Dict[str, LangfuseConfig],
        prompt_variables: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Dict[str, ExperimentResult]]:
        """
        Run a full benchmark: all configs on all prompts.

        Args:
            prompts: Dictionary of prompts
            configs: Dictionary of configs
            prompt_variables: Optional dict mapping prompt names to their variables

        Returns:
            Nested dict: {prompt_name: {config_name: result}}
        """
        all_results = {}
        prompt_variables = prompt_variables or {}

        for prompt_name, prompt in prompts.items():
            variables = prompt_variables.get(prompt_name, {})
            prompt_results = self.run_batch(
                prompt=prompt,
                configs=configs,
                prompt_variables=variables
            )
            all_results[prompt_name] = prompt_results

        return all_results
