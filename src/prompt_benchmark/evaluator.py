"""
Evaluation system for scoring experiment results.

Supports both human evaluation (via CLI) and AI evaluation (using LLM as judge).
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt as RichPrompt, FloatPrompt
from rich.table import Table

from .models import (
    Evaluation,
    EvaluationType,
    ExperimentResult,
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
