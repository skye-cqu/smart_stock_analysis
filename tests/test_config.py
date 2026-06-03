from __future__ import annotations


def test_settings_default_values():
    from src.config import Settings

    s = Settings()
    assert s.log_level in ("INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL")
    assert s.llm.temperature == 0.3
    assert s.data.akshare_rate_limit == 0.5


def test_llm_config_defaults():
    from src.config import LLMConfig

    cfg = LLMConfig()
    assert isinstance(cfg.provider, str)
    assert len(cfg.provider) > 0
    assert isinstance(cfg.model, str)
    assert isinstance(cfg.deepseek_base_url, str)
    assert isinstance(cfg.ollama_base_url, str)


def test_data_config_defaults():
    from src.config import DataConfig

    cfg = DataConfig()
    assert isinstance(cfg.sqlite_db_path, str)
    assert cfg.sqlite_db_path.endswith(".db")
    assert isinstance(cfg.cache_ttl_minutes, int)
    assert cfg.cache_ttl_minutes > 0


def test_pipeline_config_defaults():
    from src.config import PipelineConfig

    cfg = PipelineConfig()
    assert cfg.max_concurrency > 0
    assert "strategies.yaml" in cfg.strategy_config_path


def test_notification_config_defaults():
    from src.config import NotificationConfig

    cfg = NotificationConfig()
    assert isinstance(cfg.feishu_webhook_url, str)


def test_settings_singleton():
    from src.config import settings

    assert settings is not None
    assert hasattr(settings, "llm")
    assert hasattr(settings, "data")
    assert hasattr(settings, "notification")
    assert hasattr(settings, "pipeline")
