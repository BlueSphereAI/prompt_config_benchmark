"""
Configuration and prompt loader for Langfuse format configs.

Supports loading from JSON/YAML files and validating against the schema.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Union

from .models import LangfuseConfig, Prompt


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
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        configs = {}
        for file_path in directory.glob(pattern):
            # Use filename (without extension) as config name
            config_name = file_path.stem
            configs[config_name] = ConfigLoader.load_config_from_file(file_path)

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
        Load a prompt definition from a JSON or YAML file.

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
            if file_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

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
        pattern: str = "*.yaml"
    ) -> Dict[str, Prompt]:
        """
        Load all prompt files from a directory.

        Args:
            directory: Path to directory containing prompt files
            pattern: Glob pattern for prompt files (default: *.yaml)

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
        Save a prompt definition to a file.

        Args:
            prompt: Prompt to save
            file_path: Path where to save the prompt
            indent: Indentation level
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = prompt.model_dump(exclude_none=True)

        with open(file_path, 'w') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, indent=indent)
            else:
                json.dump(data, f, indent=indent)


def create_default_configs() -> Dict[str, LangfuseConfig]:
    """
    Create a set of default configurations for common use cases.

    Returns:
        Dictionary of default configurations
    """
    configs = {
        "gpt4-fast": LangfuseConfig(
            model="gpt-4-turbo-preview",
            temperature=0.3,
            max_output_tokens=500
        ),
        "gpt4-balanced": LangfuseConfig(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            max_output_tokens=1500
        ),
        "gpt4-creative": LangfuseConfig(
            model="gpt-4-turbo-preview",
            temperature=1.0,
            max_output_tokens=2000
        ),
        "gpt35-fast": LangfuseConfig(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_output_tokens=500
        ),
        "gpt35-balanced": LangfuseConfig(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_output_tokens=1500
        ),
        # GPT-5 examples (no temperature)
        "gpt5-minimal": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=600,
            verbosity="low",
            reasoning_effort="minimal"
        ),
        "gpt5-standard": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=1500,
            verbosity="medium",
            reasoning_effort="medium"
        ),
        "gpt5-thorough": LangfuseConfig(
            model="gpt-5",
            max_output_tokens=3000,
            verbosity="high",
            reasoning_effort="high"
        ),
    }
    return configs


def create_example_prompts() -> Dict[str, Prompt]:
    """
    Create example prompts for testing.

    Returns:
        Dictionary of example prompts
    """
    prompts = {
        "summarize": Prompt(
            name="summarize",
            template="Please summarize the following text concisely:\n\n{text}",
            description="Summarize a given text",
            category="text-processing",
            tags=["summarization", "text"],
            variables={"text": ""}
        ),
        "creative-story": Prompt(
            name="creative-story",
            template="Write a creative short story about {topic} in {style} style.",
            description="Generate a creative story",
            category="creative",
            tags=["creative", "story", "writing"],
            variables={"topic": "adventure", "style": "fantasy"}
        ),
        "code-review": Prompt(
            name="code-review",
            template="Review the following code and provide feedback:\n\n```{language}\n{code}\n```",
            description="Review code and provide feedback",
            category="code",
            tags=["code", "review", "programming"],
            variables={"language": "python", "code": ""}
        ),
        "explain-concept": Prompt(
            name="explain-concept",
            template="Explain {concept} to a {level} audience.",
            description="Explain a concept at different levels",
            category="education",
            tags=["education", "explanation"],
            variables={"concept": "", "level": "beginner"}
        ),
    }
    return prompts
