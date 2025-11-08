"""Tests for configuration and prompt loading."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from prompt_benchmark.config_loader import (
    ConfigLoader,
    PromptLoader,
    create_default_configs,
    create_example_prompts,
)
from prompt_benchmark.models import LangfuseConfig, Prompt


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_load_config_from_dict(self):
        """Test loading config from dictionary."""
        data = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_output_tokens": 1500
        }
        config = ConfigLoader.load_config_from_dict(data)

        assert isinstance(config, LangfuseConfig)
        assert config.model == "gpt-4"
        assert config.temperature == 0.7

    def test_load_config_from_json_file(self):
        """Test loading config from JSON file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_config.json"
            data = {
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_output_tokens": 1000
            }

            with open(config_file, 'w') as f:
                json.dump(data, f)

            config = ConfigLoader.load_config_from_file(config_file)

            assert config.model == "gpt-3.5-turbo"
            assert config.temperature == 0.5

    def test_load_configs_from_directory(self):
        """Test loading multiple configs from directory."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create multiple config files
            for i in range(3):
                config_data = {
                    "model": f"model-{i}",
                    "temperature": 0.5 + i * 0.1,
                    "max_output_tokens": 1000 + i * 100
                }
                with open(tmppath / f"config{i}.json", 'w') as f:
                    json.dump(config_data, f)

            configs = ConfigLoader.load_configs_from_directory(tmppath)

            assert len(configs) == 3
            assert "config0" in configs
            assert configs["config1"].model == "model-1"

    def test_save_config_to_file(self):
        """Test saving config to file."""
        with TemporaryDirectory() as tmpdir:
            config = LangfuseConfig(
                model="gpt-4",
                temperature=0.7,
                max_output_tokens=2000
            )

            output_file = Path(tmpdir) / "saved_config.json"
            ConfigLoader.save_config_to_file(config, output_file)

            assert output_file.exists()

            # Load it back and verify
            loaded = ConfigLoader.load_config_from_file(output_file)
            assert loaded.model == config.model
            assert loaded.temperature == config.temperature


class TestPromptLoader:
    """Test PromptLoader functionality."""

    def test_load_prompt_from_dict(self):
        """Test loading prompt from dictionary."""
        data = {
            "name": "test-prompt",
            "template": "Hello {name}",
            "description": "A test prompt"
        }
        prompt = PromptLoader.load_prompt_from_dict(data)

        assert isinstance(prompt, Prompt)
        assert prompt.name == "test-prompt"
        assert "{name}" in prompt.template

    def test_load_prompts_from_directory(self):
        """Test loading multiple prompts from directory."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create multiple prompt files (YAML)
            import yaml
            for i in range(2):
                prompt_data = {
                    "name": f"prompt-{i}",
                    "template": f"Template {i}",
                    "description": f"Description {i}"
                }
                with open(tmppath / f"prompt{i}.yaml", 'w') as f:
                    yaml.dump(prompt_data, f)

            prompts = PromptLoader.load_prompts_from_directory(tmppath)

            assert len(prompts) == 2
            assert "prompt-0" in prompts
            assert prompts["prompt-1"].description == "Description 1"

    def test_save_prompt_to_file(self):
        """Test saving prompt to file."""
        with TemporaryDirectory() as tmpdir:
            prompt = Prompt(
                name="test",
                template="Hello {name}",
                description="Test prompt",
                tags=["test"]
            )

            output_file = Path(tmpdir) / "saved_prompt.yaml"
            PromptLoader.save_prompt_to_file(prompt, output_file)

            assert output_file.exists()

            # Load it back
            loaded = PromptLoader.load_prompt_from_file(output_file)
            assert loaded.name == prompt.name
            assert loaded.template == prompt.template


class TestDefaultCreators:
    """Test default config and prompt creators."""

    def test_create_default_configs(self):
        """Test creating default configurations."""
        configs = create_default_configs()

        assert len(configs) > 0
        assert "gpt4-balanced" in configs
        assert configs["gpt4-balanced"].model == "gpt-4-turbo-preview"

    def test_create_example_prompts(self):
        """Test creating example prompts."""
        prompts = create_example_prompts()

        assert len(prompts) > 0
        assert "summarize" in prompts
        assert "creative-story" in prompts
        assert prompts["summarize"].category == "text-processing"
