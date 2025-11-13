"""
Evaluation system for scoring experiment results.

Supports both human evaluation (via CLI) and AI evaluation (using LLM as judge).
Includes batch AI evaluation system with review prompt templates.
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from openai import AsyncOpenAI, OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt as RichPrompt, FloatPrompt
from rich.table import Table

from .models import (
    AIEvaluation,
    AIEvaluationBatch,
    Evaluation,
    EvaluationType,
    ExperimentResult,
    ReviewPrompt,
)
from .storage import ResultStorage


console = Console()


class HumanEvaluator:
    """
    Interactive CLI for human evaluation of results.

    Presents results to humans for scoring and feedback.
    """

    def __init__(self, storage: ResultStorage):
        """
        Initialize the human evaluator.

        Args:
            storage: Storage instance for saving evaluations
        """
        self.storage = storage

    def evaluate_result(
        self,
        result: ExperimentResult,
        evaluator_name: Optional[str] = None,
        criteria: Optional[List[str]] = None
    ) -> Evaluation:
        """
        Interactively evaluate a single result.

        Args:
            result: The experiment result to evaluate
            evaluator_name: Name of the human evaluator
            criteria: List of criteria to score (optional)

        Returns:
            Evaluation object
        """
        console.clear()
        console.print(Panel.fit(
            f"[bold cyan]Evaluating Experiment[/bold cyan]\n\n"
            f"Prompt: {result.prompt_name}\n"
            f"Config: {result.config_name}",
            title="Experiment Details"
        ))

        # Show the prompt
        console.print("\n[bold]Prompt:[/bold]")
        console.print(Panel(result.rendered_prompt, border_style="blue"))

        # Show the response
        console.print("\n[bold]Response:[/bold]")
        console.print(Panel(result.response, border_style="green"))

        # Show metrics
        console.print("\n[bold]Metrics:[/bold]")
        metrics_table = Table(show_header=False, box=None)
        metrics_table.add_row("Duration:", f"{result.duration_seconds:.2f}s")
        if result.total_tokens:
            metrics_table.add_row("Tokens:", str(result.total_tokens))
        if result.estimated_cost_usd:
            metrics_table.add_row("Est. Cost:", f"${result.estimated_cost_usd:.6f}")
        console.print(metrics_table)

        # Get overall score
        console.print("\n[bold yellow]Overall Evaluation[/bold yellow]")
        overall_score = FloatPrompt.ask(
            "Overall score (0-10)",
            default=5.0
        )
        while overall_score < 0 or overall_score > 10:
            console.print("[red]Score must be between 0 and 10[/red]")
            overall_score = FloatPrompt.ask("Overall score (0-10)", default=5.0)

        # Get criteria scores if provided
        criteria_scores = {}
        if criteria:
            console.print("\n[bold yellow]Criteria Scores[/bold yellow]")
            for criterion in criteria:
                score = FloatPrompt.ask(
                    f"{criterion} (0-10)",
                    default=overall_score
                )
                while score < 0 or score > 10:
                    console.print("[red]Score must be between 0 and 10[/red]")
                    score = FloatPrompt.ask(f"{criterion} (0-10)", default=overall_score)
                criteria_scores[criterion] = score

        # Get feedback
        console.print("\n[bold yellow]Feedback[/bold yellow]")
        notes = RichPrompt.ask("Notes (optional)", default="")
        strengths = RichPrompt.ask("Strengths (optional)", default="")
        weaknesses = RichPrompt.ask("Weaknesses (optional)", default="")

        # Create evaluation
        evaluation = Evaluation(
            id=str(uuid.uuid4()),
            experiment_id=result.experiment_id,
            evaluation_type=EvaluationType.HUMAN,
            evaluator_name=evaluator_name or "anonymous",
            score=overall_score,
            criteria=criteria_scores,
            notes=notes if notes else None,
            strengths=strengths if strengths else None,
            weaknesses=weaknesses if weaknesses else None
        )

        # Save to storage
        self.storage.save_evaluation(evaluation)

        console.print("\n[green]Evaluation saved![/green]")
        return evaluation

    def evaluate_batch(
        self,
        results: List[ExperimentResult],
        evaluator_name: Optional[str] = None,
        criteria: Optional[List[str]] = None
    ) -> List[Evaluation]:
        """
        Evaluate multiple results interactively.

        Args:
            results: List of results to evaluate
            evaluator_name: Name of the evaluator
            criteria: Criteria to score

        Returns:
            List of Evaluation objects
        """
        evaluations = []

        if not evaluator_name:
            evaluator_name = RichPrompt.ask(
                "Enter your name",
                default="anonymous"
            )

        console.print(f"\n[bold]Evaluating {len(results)} results[/bold]\n")

        for i, result in enumerate(results, 1):
            console.print(f"[cyan]Result {i}/{len(results)}[/cyan]")
            evaluation = self.evaluate_result(result, evaluator_name, criteria)
            evaluations.append(evaluation)

            if i < len(results):
                continue_eval = RichPrompt.ask(
                    "\nContinue to next result?",
                    choices=["y", "n"],
                    default="y"
                )
                if continue_eval.lower() != "y":
                    break

        return evaluations


class AIEvaluator:
    """
    AI-based evaluation using LLM as a judge.

    Uses an LLM to score and provide feedback on experiment results.
    """

    def __init__(
        self,
        storage: ResultStorage,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Initialize the AI evaluator.

        Args:
            storage: Storage instance for saving evaluations
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use as judge (defaults to EVALUATOR_MODEL or gpt-4)
            temperature: Temperature for evaluation (lower = more consistent)
        """
        self.storage = storage
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("EVALUATOR_MODEL", "gpt-4")
        self.temperature = temperature

        if not self.api_key:
            raise ValueError("OpenAI API key required for AI evaluation")

        self.client = OpenAI(api_key=self.api_key)

    def evaluate_result(
        self,
        result: ExperimentResult,
        criteria: Optional[List[str]] = None,
        evaluation_prompt: Optional[str] = None
    ) -> Evaluation:
        """
        Evaluate a result using an LLM.

        Args:
            result: The experiment result to evaluate
            criteria: Specific criteria to evaluate
            evaluation_prompt: Custom evaluation prompt (optional)

        Returns:
            Evaluation object
        """
        # Build evaluation prompt
        if not evaluation_prompt:
            evaluation_prompt = self._build_default_prompt(result, criteria)

        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator. Provide objective, "
                                   "detailed assessments of LLM outputs."
                    },
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=self.temperature
            )

            evaluation_text = response.choices[0].message.content

            # Parse the evaluation (expecting JSON format)
            import json
            eval_data = self._parse_evaluation_response(evaluation_text)

            # Create evaluation object
            evaluation = Evaluation(
                id=str(uuid.uuid4()),
                experiment_id=result.experiment_id,
                evaluation_type=EvaluationType.AI,
                evaluator_name=self.model,
                score=eval_data.get("score", 5.0),
                criteria=eval_data.get("criteria", {}),
                notes=eval_data.get("notes"),
                strengths=eval_data.get("strengths"),
                weaknesses=eval_data.get("weaknesses")
            )

            # Save to storage
            self.storage.save_evaluation(evaluation)

            return evaluation

        except Exception as e:
            console.print(f"[red]AI evaluation failed: {e}[/red]")
            # Return a default evaluation
            return Evaluation(
                id=str(uuid.uuid4()),
                experiment_id=result.experiment_id,
                evaluation_type=EvaluationType.AI,
                evaluator_name=self.model,
                score=0.0,
                notes=f"Evaluation failed: {e}"
            )

    def evaluate_batch(
        self,
        results: List[ExperimentResult],
        criteria: Optional[List[str]] = None
    ) -> List[Evaluation]:
        """
        Evaluate multiple results using AI.

        Args:
            results: List of results to evaluate
            criteria: Criteria to evaluate

        Returns:
            List of Evaluation objects
        """
        evaluations = []
        for result in results:
            evaluation = self.evaluate_result(result, criteria)
            evaluations.append(evaluation)
        return evaluations

    def _build_default_prompt(
        self,
        result: ExperimentResult,
        criteria: Optional[List[str]] = None
    ) -> str:
        """Build a default evaluation prompt."""
        prompt = f"""Please evaluate the following LLM output.

**Original Prompt:**
{result.rendered_prompt}

**LLM Response:**
{result.response}

**Response Metadata:**
- Model: {result.config.model}
- Temperature: {result.config.temperature}
- Duration: {result.duration_seconds:.2f}s
- Tokens: {result.total_tokens or 'N/A'}

"""

        if criteria:
            prompt += f"\n**Evaluation Criteria:**\n"
            for criterion in criteria:
                prompt += f"- {criterion}\n"

        prompt += """
**Please provide your evaluation in the following JSON format:**

```json
{
  "score": <overall score 0-10>,
  "criteria": {
    "accuracy": <score 0-10>,
    "relevance": <score 0-10>,
    "coherence": <score 0-10>,
    "completeness": <score 0-10>
  },
  "strengths": "<what the response does well>",
  "weaknesses": "<what could be improved>",
  "notes": "<any additional observations>"
}
```

Focus on:
1. How well the response addresses the prompt
2. Quality and accuracy of the information
3. Clarity and coherence of the writing
4. Completeness of the answer
"""
        return prompt

    def _parse_evaluation_response(self, response_text: str) -> Dict:
        """Parse the AI's evaluation response."""
        import json
        import re

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                # Fallback: return default structure
                return {
                    "score": 5.0,
                    "notes": response_text
                }

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return {
                "score": 5.0,
                "notes": response_text
            }


# ============================================================================
# Batch AI Evaluation System
# ============================================================================


async def batch_evaluate_prompt(
    prompt_name: str,
    review_prompt: ReviewPrompt,
    evaluator_model: str,
    storage: ResultStorage,
    parallel: bool = True,  # Kept for API compatibility, but not used with single-call approach
    run_id: Optional[str] = None
) -> AIEvaluationBatch:
    """
    Evaluate all experiments for a prompt using AI with comparative ranking.

    Sends ALL responses to the AI in a single call for comparative evaluation.

    Args:
        prompt_name: Name of prompt to evaluate
        review_prompt: Review prompt template to use
        evaluator_model: Model to use for evaluation (e.g., "gpt-5")
        storage: Database storage
        parallel: Unused (kept for API compat), evaluation is now single comparative call
        run_id: Optional run ID to filter experiments to specific run

    Returns:
        AIEvaluationBatch with all evaluations and rankings
    """
    # 1. Get all successful experiments for this prompt (filter by run if provided)
    if run_id:
        experiments = storage.get_results_by_run(run_id)
        experiments = [exp for exp in experiments if exp.success]
    else:
        experiments = storage.get_results_by_prompt(prompt_name, success_only=True)

    if not experiments:
        raise ValueError(f"No successful experiments found for prompt: {prompt_name}")

    # 2. Create batch record
    batch = AIEvaluationBatch(
        batch_id=str(uuid.uuid4()),
        prompt_name=prompt_name,
        review_prompt_id=review_prompt.prompt_id,
        model_evaluator=evaluator_model,
        status="running",
        num_experiments=len(experiments),
        num_completed=0,
        started_at=datetime.utcnow()
    )
    storage.save_ai_batch(batch)

    # 3. Build prompt with ALL responses for comparative evaluation
    # Get the original prompt from first experiment
    original_prompt = experiments[0].rendered_prompt if experiments else ""

    # Format all responses
    all_responses_text = ""
    for i, exp in enumerate(experiments, 1):
        all_responses_text += f"\n--- CONFIGURATION {i}: {exp.config_name} ---\n"
        all_responses_text += f"{exp.response}\n"

    # Fill in template variables
    evaluation_prompt = review_prompt.template.format(
        original_prompt=original_prompt,
        num_configs=len(experiments),
        all_responses=all_responses_text
    )

    # 4. Make SINGLE API call with ALL responses for comparative ranking
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        client = AsyncOpenAI(api_key=api_key)

        # Use GPT-5 with reasoning for best evaluation
        messages = [
            {"role": "system", "content": review_prompt.system_prompt},
            {"role": "user", "content": evaluation_prompt}
        ]

        # Build API params - GPT-5 doesn't support temperature parameter
        api_params = {
            "model": evaluator_model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }

        # Only add temperature for non-GPT-5 models
        if not evaluator_model.startswith("gpt-5"):
            api_params["temperature"] = 0.3
        else:
            # Add GPT-5 specific parameters for high-quality evaluation
            api_params["reasoning_effort"] = "high"
            api_params["verbosity"] = "medium"

        response = await client.chat.completions.create(**api_params)

        # Parse the comparative rankings
        result_json = json.loads(response.choices[0].message.content)
        rankings_list = result_json.get("rankings", [])

        # 5. Create AIEvaluation objects from rankings
        evaluations = []
        config_to_experiment = {exp.config_name: exp for exp in experiments}

        # Debug logging
        console.print(f"[blue]AI returned {len(rankings_list)} rankings[/blue]")
        console.print(f"[blue]Expected config names: {list(config_to_experiment.keys())[:5]}...[/blue]")

        unmatched_configs = []
        for ranking_data in rankings_list:
            config_name = ranking_data.get("config_name", "")
            experiment = config_to_experiment.get(config_name)

            # Try fuzzy matching if exact match fails
            if not experiment:
                # Try case-insensitive match
                for exp_name, exp in config_to_experiment.items():
                    if exp_name.lower() == config_name.lower():
                        experiment = exp
                        console.print(f"[cyan]Fuzzy matched: '{config_name}' -> '{exp_name}'[/cyan]")
                        break

                # Try partial match (in case AI abbreviated)
                if not experiment:
                    for exp_name, exp in config_to_experiment.items():
                        if config_name.lower() in exp_name.lower() or exp_name.lower() in config_name.lower():
                            experiment = exp
                            console.print(f"[cyan]Partial match: '{config_name}' -> '{exp_name}'[/cyan]")
                            break

            if not experiment:
                unmatched_configs.append(config_name)
                console.print(f"[yellow]Warning: AI ranked unknown config: '{config_name}'[/yellow]")
                continue

            evaluation = AIEvaluation(
                evaluation_id=str(uuid.uuid4()),
                experiment_id=experiment.experiment_id,
                review_prompt_id=review_prompt.prompt_id,
                batch_id=batch.batch_id,
                model_evaluator=evaluator_model,
                criteria_scores=ranking_data.get("criteria_scores", {}),
                overall_score=ranking_data.get("overall_score", 5.0),
                ai_rank=ranking_data.get("rank", 0),
                justification=ranking_data.get("comment", ""),
                strengths=[ranking_data.get("comment", "")],  # Store comment as strength
                weaknesses=[],
                evaluated_at=datetime.utcnow(),
                evaluation_duration=0.0  # Single call, not per-experiment timing
            )
            evaluations.append(evaluation)

        # 6. Check if we have any evaluations
        if len(evaluations) == 0:
            error_msg = f"AI evaluation failed: No evaluations created. "
            if unmatched_configs:
                error_msg += f"AI returned config names that didn't match experiments: {unmatched_configs[:5]}"
            console.print(f"[red]{error_msg}[/red]")

            # Update batch as failed
            batch.status = "failed"
            batch.completed_at = datetime.utcnow()
            storage.update_ai_batch(batch)
            raise ValueError(error_msg)

        # 7. Save all evaluations
        for eval in evaluations:
            storage.save_ai_evaluation(eval)

        console.print(f"[green]Successfully created {len(evaluations)} evaluations[/green]")

        # 8. Update batch as completed
        batch.status = "completed"
        batch.num_completed = len(evaluations)
        batch.completed_at = datetime.utcnow()
        batch.total_duration = (batch.completed_at - batch.started_at).total_seconds()
        batch.evaluation_ids = [e.evaluation_id for e in evaluations]
        batch.ranked_experiment_ids = [e.experiment_id for e in evaluations]
        storage.update_ai_batch(batch)

        # 9. Update run status to analysis_completed if run_id was provided
        if run_id:
            storage.update_run_status(run_id, status="analysis_completed")
            console.print(f"[green]Updated run {run_id} status to 'analysis_completed'[/green]")

        return batch

    except Exception as e:
        # Update batch as failed
        batch.status = "failed"
        batch.completed_at = datetime.utcnow()
        storage.update_ai_batch(batch)
        raise ValueError(f"AI evaluation failed: {str(e)}")


async def evaluate_single_experiment(
    experiment: ExperimentResult,
    review_prompt: ReviewPrompt,
    evaluator_model: str,
    batch_id: str,
    storage: ResultStorage
) -> AIEvaluation:
    """
    Evaluate a single experiment using AI.

    Args:
        experiment: Experiment to evaluate
        review_prompt: Review prompt template
        evaluator_model: Model to use for evaluation
        batch_id: Batch ID this evaluation belongs to
        storage: Database storage (for API key)

    Returns:
        AIEvaluation object
    """
    # Render the review prompt
    rendered_prompt = review_prompt.template.format(
        original_prompt=experiment.rendered_prompt,
        config_name=experiment.config_name,
        result=experiment.response
    )

    # Call evaluator LLM
    start_time = time.time()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = AsyncOpenAI(api_key=api_key)

    try:
        # Build API params - GPT-5 doesn't support temperature parameter
        api_params = {
            "model": evaluator_model,
            "messages": [
                {
                    "role": "system",
                    "content": review_prompt.system_prompt or "You are an expert evaluator."
                },
                {"role": "user", "content": rendered_prompt}
            ],
            "response_format": {"type": "json_object"}  # Ensure JSON response
        }

        # Only add temperature for non-GPT-5 models
        if not evaluator_model.startswith("gpt-5"):
            api_params["temperature"] = 0.3  # Lower temperature for more consistent evaluations
        else:
            # Add GPT-5 specific parameters for high-quality evaluation
            api_params["reasoning_effort"] = "high"
            api_params["verbosity"] = "medium"

        response = await client.chat.completions.create(**api_params)

        duration = time.time() - start_time

        # Parse response
        eval_data = json.loads(response.choices[0].message.content)

        # Create evaluation object
        evaluation = AIEvaluation(
            evaluation_id=str(uuid.uuid4()),
            experiment_id=experiment.experiment_id,
            review_prompt_id=review_prompt.prompt_id,
            batch_id=batch_id,
            model_evaluator=evaluator_model,
            criteria_scores=eval_data.get("criteria_scores", {}),
            overall_score=float(eval_data.get("overall_score", 5.0)),
            ai_rank=0,  # Will be set later
            justification=eval_data.get("justification", ""),
            strengths=eval_data.get("key_strengths", []),
            weaknesses=eval_data.get("key_weaknesses", []),
            evaluated_at=datetime.utcnow(),
            evaluation_duration=duration
        )

        return evaluation

    except Exception as e:
        # Return a failed evaluation
        console.print(f"[red]Evaluation failed for {experiment.config_name}: {e}[/red]")
        return AIEvaluation(
            evaluation_id=str(uuid.uuid4()),
            experiment_id=experiment.experiment_id,
            review_prompt_id=review_prompt.prompt_id,
            batch_id=batch_id,
            model_evaluator=evaluator_model,
            criteria_scores={},
            overall_score=0.0,
            ai_rank=999,
            justification=f"Evaluation failed: {str(e)}",
            strengths=[],
            weaknesses=[],
            evaluated_at=datetime.utcnow(),
            evaluation_duration=time.time() - start_time
        )


def run_batch_evaluation(
    prompt_name: str,
    review_prompt: ReviewPrompt,
    evaluator_model: str,
    storage: ResultStorage,
    parallel: bool = True,
    run_id: Optional[str] = None
) -> AIEvaluationBatch:
    """
    Synchronous wrapper for batch_evaluate_prompt.

    Args:
        prompt_name: Name of prompt to evaluate
        review_prompt: Review prompt template to use
        evaluator_model: Model to use for evaluation
        storage: Database storage
        parallel: Run evaluations in parallel
        run_id: Optional run ID to filter experiments

    Returns:
        AIEvaluationBatch with results
    """
    return asyncio.run(
        batch_evaluate_prompt(
            prompt_name, review_prompt, evaluator_model, storage, parallel, run_id
        )
    )
