from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class LLMConfig:
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "deepseek"))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "deepseek/deepseek-chat"))
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:14b"))
    temperature: float = 0.3


@dataclass
class DataConfig:
    tushare_token: str = field(default_factory=lambda: os.getenv("TUSHARE_TOKEN", ""))
    sqlite_db_path: str = field(
        default_factory=lambda: os.getenv(
            "SQLITE_DB_PATH", str(PROJECT_ROOT / "data" / "sqlite" / "stock.db")
        )
    )
    cache_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_MINUTES", "5")))
    akshare_rate_limit: float = 0.5


@dataclass
class NotificationConfig:
    feishu_webhook_url: str = field(default_factory=lambda: os.getenv("FEISHU_WEBHOOK_URL", ""))


@dataclass
class PipelineConfig:
    max_concurrency: int = field(
        default_factory=lambda: int(os.getenv("ANALYSIS_MAX_CONCURRENCY", "5"))
    )
    strategy_config_path: str = field(
        default_factory=lambda: str(PROJECT_ROOT / "configs" / "strategies.yaml")
    )


@dataclass
class Settings:
    llm: LLMConfig = field(default_factory=LLMConfig)
    data: DataConfig = field(default_factory=DataConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()
