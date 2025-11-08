"""
Experiment executor for running LLM prompts with timing and metrics collection.

Handles OpenAI API calls, measures performance, and captures results.
"""

import asyncio
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from openai import AsyncOpenAI, OpenAI
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
        self.async_client = AsyncOpenAI(api_key=self.api_key)

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

        # Get messages from prompt
        messages = prompt.get_messages()

        # Store rendered prompt as string for display
        rendered_prompt = prompt.to_string()

        # Prepare API call parameters
        api_params = self._prepare_api_params(config, messages)

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

    async def run_experiment_async(
        self,
        prompt: Prompt,
        config: LangfuseConfig,
        config_name: str,
        prompt_variables: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> ExperimentResult:
        """
        Run a single experiment asynchronously.

        Args:
            prompt: The prompt to use
            config: The LLM configuration
            config_name: Human-readable name for this config
            prompt_variables: Variables to fill in the prompt template (unused for messages format)
            metadata: Additional metadata to store

        Returns:
            ExperimentResult with timing and metrics
        """
        # Generate experiment ID
        experiment_id = str(uuid.uuid4())

        # Get messages from prompt
        messages = prompt.get_messages()

        # Store rendered prompt as string for display
        rendered_prompt = prompt.to_string()

        # Prepare API call parameters
        api_params = self._prepare_api_params(config, messages)

        # Execute with timing
        start_time = datetime.utcnow()
        start_perf = time.perf_counter()

        try:
            completion = await self.async_client.chat.completions.create(**api_params)
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

    def _prepare_api_params(self, config: LangfuseConfig, messages: List[Dict[str, str]]) -> Dict:
        """
        Prepare OpenAI API parameters from Langfuse config.

        Args:
            config: Langfuse configuration
            messages: List of message dictionaries with role and content

        Returns:
            Dictionary of API parameters
        """
        params = {
            "model": config.model,
            "messages": messages,
        }

        # Add optional parameters if present
        if config.temperature is not None and not config.model.startswith("gpt-5"):
            params["temperature"] = config.temperature

        # GPT-5 uses max_completion_tokens, other models use max_tokens
        if config.max_output_tokens is not None:
            if config.model.startswith("gpt-5"):
                params["max_completion_tokens"] = config.max_output_tokens
            else:
                params["max_tokens"] = config.max_output_tokens

        if config.top_p is not None:
            params["top_p"] = config.top_p

        if config.frequency_penalty is not None:
            params["frequency_penalty"] = config.frequency_penalty

        if config.presence_penalty is not None:
            params["presence_penalty"] = config.presence_penalty

        # GPT-5 specific parameters
        # Note: verbosity and reasoning_effort are stored in config but
        # the actual API parameters may differ - adjust based on OpenAI docs
        if config.model.startswith("gpt-5"):
            if config.verbosity is not None:
                # Map to actual API parameter when available
                pass  # TODO: Update when API supports this
            if config.reasoning_effort is not None:
                # Map to actual API parameter when available
                pass  # TODO: Update when API supports this

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
            finish_reason = choice.finish_reason

            # Handle different message formats
            if choice.message:
                if choice.message.content:
                    response_text = choice.message.content
                # Some models might use refusal or other fields
                elif hasattr(choice.message, 'refusal') and choice.message.refusal:
                    response_text = f"[REFUSAL] {choice.message.refusal}"
                # Check for tool calls or function calls
                elif hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    response_text = f"[TOOL_CALLS] {choice.message.tool_calls}"

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
        Run multiple experiments with different configs on the same prompt in parallel.

        Args:
            prompt: The prompt to use
            configs: Dictionary mapping config names to LangfuseConfig instances
            prompt_variables: Variables for the prompt
            metadata: Additional metadata

        Returns:
            Dictionary mapping config names to results
        """
        return asyncio.run(self.run_batch_async(prompt, configs, prompt_variables, metadata))

    async def run_batch_async(
        self,
        prompt: Prompt,
        configs: Dict[str, LangfuseConfig],
        prompt_variables: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, ExperimentResult]:
        """
        Run multiple experiments with different configs on the same prompt in parallel (async).

        Args:
            prompt: The prompt to use
            configs: Dictionary mapping config names to LangfuseConfig instances
            prompt_variables: Variables for the prompt
            metadata: Additional metadata

        Returns:
            Dictionary mapping config names to results
        """
        # Create tasks for all experiments
        tasks = []
        config_names = []
        for config_name, config in configs.items():
            task = self.run_experiment_async(
                prompt=prompt,
                config=config,
                config_name=config_name,
                prompt_variables=prompt_variables,
                metadata=metadata
            )
            tasks.append(task)
            config_names.append(config_name)

        # Run all tasks in parallel
        results_list = await asyncio.gather(*tasks)

        # Map results back to config names
        results = {name: result for name, result in zip(config_names, results_list)}

        return results

    def run_full_benchmark(
        self,
        prompts: Dict[str, Prompt],
        configs: Dict[str, LangfuseConfig],
        prompt_variables: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Dict[str, ExperimentResult]]:
        """
        Run a full benchmark: all configs on all prompts in parallel.

        Args:
            prompts: Dictionary of prompts
            configs: Dictionary of configs
            prompt_variables: Optional dict mapping prompt names to their variables

        Returns:
            Nested dict: {prompt_name: {config_name: result}}
        """
        return asyncio.run(self.run_full_benchmark_async(prompts, configs, prompt_variables))

    async def run_full_benchmark_async(
        self,
        prompts: Dict[str, Prompt],
        configs: Dict[str, LangfuseConfig],
        prompt_variables: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Dict[str, ExperimentResult]]:
        """
        Run a full benchmark: all configs on all prompts in parallel (async).

        Args:
            prompts: Dictionary of prompts
            configs: Dictionary of configs
            prompt_variables: Optional dict mapping prompt names to their variables

        Returns:
            Nested dict: {prompt_name: {config_name: result}}
        """
        prompt_variables = prompt_variables or {}

        # Create tasks for all prompt batches
        tasks = []
        prompt_names = []
        for prompt_name, prompt in prompts.items():
            variables = prompt_variables.get(prompt_name, {})
            task = self.run_batch_async(
                prompt=prompt,
                configs=configs,
                prompt_variables=variables
            )
            tasks.append(task)
            prompt_names.append(prompt_name)

        # Run all prompt batches in parallel
        results_list = await asyncio.gather(*tasks)

        # Map results back to prompt names
        all_results = {name: results for name, results in zip(prompt_names, results_list)}

        return all_results
