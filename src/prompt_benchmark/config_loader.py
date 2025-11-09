"""
Configuration and prompt loader for Langfuse format configs.

Supports loading from JSON/YAML files and validating against the schema.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Union

from .models import LangfuseConfig, Prompt

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and validate Langfuse-format configurations."""

    @staticmethod
    def load_config_from_file(file_path: Union[str, Path]) -> LangfuseConfig:
        """
        Load a single Langfuse configuration from a JSON or YAML file.

        Args:
            file_path: Path to the configuration file

        Returns:
            Validated LangfuseConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If config is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        # Load based on file extension
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return LangfuseConfig(**data)

    @staticmethod
    def load_config_from_dict(data: Dict) -> LangfuseConfig:
        """
        Load a Langfuse configuration from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Validated LangfuseConfig instance
        """
        return LangfuseConfig(**data)

    @staticmethod
    def load_configs_from_directory(
        directory: Union[str, Path],
        pattern: str = "*.json"
    ) -> Dict[str, LangfuseConfig]:
        """
        Load all configuration files from a directory.

        Args:
            directory: Path to directory containing config files
            pattern: Glob pattern for config files (default: *.json)

        Returns:
            Dictionary mapping config names to LangfuseConfig instances
        """
        directory = Path(directory)
        logger.info(f"Loading configs from directory: {directory} with pattern: {pattern}")

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            raise FileNotFoundError(f"Directory not found: {directory}")

        configs = {}
        config_files = list(directory.glob(pattern))
        logger.info(f"Found {len(config_files)} config files matching pattern '{pattern}'")

        for file_path in config_files:
            # Use filename (without extension) as config name
            config_name = file_path.stem
            try:
                logger.debug(f"Loading config from file: {file_path}")
                config = ConfigLoader.load_config_from_file(file_path)
                configs[config_name] = config
                logger.info(f"Successfully loaded config '{config_name}' from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {file_path}: {str(e)}", exc_info=True)
                raise

        logger.info(f"Loaded {len(configs)} configs total: {list(configs.keys())}")
        return configs

    @staticmethod
    def save_config_to_file(
        config: LangfuseConfig,
        file_path: Union[str, Path],
        indent: int = 2
    ) -> None:
        """
        Save a Langfuse configuration to a file.

        Args:
            config: Configuration to save
            file_path: Path where to save the config
            indent: JSON indentation level
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict, excluding None values for cleaner output
        data = config.model_dump(exclude_none=True)

        with open(file_path, 'w') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, indent=indent)
            else:
                json.dump(data, f, indent=indent)


class PromptLoader:
    """Load and manage prompt definitions."""

    @staticmethod
    def load_prompt_from_file(file_path: Union[str, Path]) -> Prompt:
        """
        Load a prompt definition from a JSON file.

        The file should contain either:
        1. A list of message objects (OpenAI messages format)
        2. A dict with 'name', 'messages', and optional metadata

        Args:
            file_path: Path to the prompt file

        Returns:
            Validated Prompt instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If prompt is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, 'r') as f:
            data = json.load(f)

        # If data is a list, it's just the messages array
        if isinstance(data, list):
            # Extract name from filename
            prompt_name = file_path.stem
            return Prompt(name=prompt_name, messages=data)

        # Otherwise, expect a dict with name and messages
        return Prompt(**data)

    @staticmethod
    def load_prompt_from_dict(data: Dict) -> Prompt:
        """
        Load a prompt from a dictionary.

        Args:
            data: Prompt dictionary

        Returns:
            Validated Prompt instance
        """
        return Prompt(**data)

    @staticmethod
    def load_prompts_from_directory(
        directory: Union[str, Path],
        pattern: str = "*.json"
    ) -> Dict[str, Prompt]:
        """
        Load all prompt files from a directory.

        Args:
            directory: Path to directory containing prompt files
            pattern: Glob pattern for prompt files (default: *.json)

        Returns:
            Dictionary mapping prompt names to Prompt instances
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        prompts = {}
        for file_path in directory.glob(pattern):
            prompt = PromptLoader.load_prompt_from_file(file_path)
            prompts[prompt.name] = prompt

        return prompts

    @staticmethod
    def save_prompt_to_file(
        prompt: Prompt,
        file_path: Union[str, Path],
        indent: int = 2
    ) -> None:
        """
        Save a prompt definition to a JSON file.

        Args:
            prompt: Prompt to save
            file_path: Path where to save the prompt
            indent: Indentation level
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = prompt.model_dump(exclude_none=True)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)


def create_default_configs() -> Dict[str, LangfuseConfig]:
    """
    Create a set of default GPT-5 configurations for common use cases.

    Returns:
        Dictionary of default configurations
    """
    configs = {
        # GPT-5 Mini variants (faster, lower cost)
        "gpt5-mini-fast": LangfuseConfig(
            model="gpt-5-mini",
            max_output_tokens=500,
            verbosity="low",
            reasoning_effort="minimal"
        ),
        "gpt5-mini-balanced": LangfuseConfig(
            model="gpt-5-mini",
            max_output_tokens=1000,
            verbosity="medium",
            reasoning_effort="medium"
        ),
        # GPT-5 standard variants
        "gpt5-minimal": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=600,
            verbosity="low",
            reasoning_effort="minimal"
        ),
        "gpt5-concise": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=800,
            verbosity="low",
            reasoning_effort="medium"
        ),
        "gpt5-compact": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=600,
            verbosity="low",
            reasoning_effort="high"
        ),
        "gpt5-standard": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=1500,
            verbosity="medium",
            reasoning_effort="medium"
        ),
        "gpt5-balanced-high-reasoning": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=1500,
            verbosity="medium",
            reasoning_effort="high"
        ),
        "gpt5-detailed": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=2000,
            verbosity="high",
            reasoning_effort="medium"
        ),
        "gpt5-verbose": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=2500,
            verbosity="high",
            reasoning_effort="minimal"
        ),
        "gpt5-thorough": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=3000,
            verbosity="high",
            reasoning_effort="high"
        ),
        "gpt5-extended": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=4000,
            verbosity="high",
            reasoning_effort="high"
        ),
    }
    return configs


def create_example_prompts() -> Dict[str, Prompt]:
    """
    Create example prompts for testing in OpenAI messages format.

    Returns:
        Dictionary of example prompts
    """
    prompts = {
        "simple-summary": Prompt(
            name="simple-summary",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries."
                },
                {
                    "role": "user",
                    "content": "Please summarize the following text in 2-3 sentences:\n\nArtificial intelligence has made remarkable progress in recent years, with breakthroughs in natural language processing, computer vision, and machine learning. These advances are transforming industries from healthcare to finance."
                }
            ],
            description="Simple text summarization",
            category="text-processing",
            tags=["summarization", "text"]
        ),
        "creative-writing": Prompt(
            name="creative-writing",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative writer specializing in short fiction."
                },
                {
                    "role": "user",
                    "content": "Write a 100-word story about a robot discovering emotions for the first time."
                }
            ],
            description="Creative story generation",
            category="creative",
            tags=["creative", "story", "writing"]
        ),
        "technical-explanation": Prompt(
            name="technical-explanation",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical educator who explains complex concepts clearly."
                },
                {
                    "role": "user",
                    "content": "Explain how neural networks work to a high school student in simple terms."
                }
            ],
            description="Explain technical concepts simply",
            category="education",
            tags=["education", "explanation", "technical"]
        ),
    }
    return prompts
