"""Configuration loader — merges .env secrets + agent.yaml into typed Settings."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# --- YAML config models ---

class AgentConfig(BaseModel):
    name: str = "harness-agent"
    model: str = "openai/gpt-4o-mini"
    fallback_model: str = "openai/gpt-4o-mini"


class ScopeConfig(BaseModel):
    enabled: bool = False
    description: str = ""
    rejection_message: str = "Sorry, that's outside my scope."


class LimitsConfig(BaseModel):
    max_iterations: int = 10
    max_cost_usd: float = 0.50
    timeout_seconds: int = 120
    max_tool_output_chars: int = 8000


class ToolsConfig(BaseModel):
    enabled: list[str] = Field(default_factory=lambda: ["calculator"])


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_file: str | None = "agent.log"


class DatabaseConfig(BaseModel):
    path: str = "agent_harness.db"  # Local SQLite file
    url: str | None = None  # Override: external DB connection string


class AgentYamlConfig(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    instructions: str = "You are a helpful assistant."
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# --- Environment secrets ---

class EnvSecrets(BaseSettings):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    tavily_api_key: str | None = None
    openrouter_api_key: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


# --- Merged settings ---

class Settings(BaseModel):
    yaml_config: AgentYamlConfig
    secrets: EnvSecrets


def api_key_for_model(model: str, secrets: EnvSecrets) -> str | None:
    """Return the configured API key for a LiteLLM model identifier."""
    provider = model.split("/", 1)[0].lower()
    keys = {
        "openrouter": secrets.openrouter_api_key,
        "openai": secrets.openai_api_key,
        "anthropic": secrets.anthropic_api_key,
        "gemini": secrets.gemini_api_key,
    }
    return keys.get(provider)


def load_settings(config_path: str = "agent.yaml") -> Settings:
    """Load settings from agent.yaml + .env file."""
    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        yaml_config = AgentYamlConfig(**raw)
    else:
        yaml_config = AgentYamlConfig()

    secrets = EnvSecrets()
    return Settings(yaml_config=yaml_config, secrets=secrets)
