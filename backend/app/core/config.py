from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "justice-risk-platform"
    app_env: Literal["dev", "test", "prod"] = "dev"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./justice_risk.db"

    embedding_provider: Literal["local", "openai", "hash"] = "hash"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimension: int = 384

    llm_provider: Literal["anthropic", "openai", "echo"] = "echo"
    llm_model: str = "Qwen/Qwen3-14B"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    llm_timeout_seconds: int = 45
    llm_force_json_object: bool = True
    llm_disable_thinking: bool = True

    knowledge_top_k: int = 5
    knowledge_semantic_weight: float = Field(default=0.65, ge=0.0, le=1.0)
    knowledge_keyword_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    knowledge_exclude_demo_articles: bool = True

    case_corpus_top_k: int = 5
    analysis_semantic_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    analysis_keyword_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    analysis_law_candidate_pool_size: int = Field(default=12, ge=3, le=30)
    analysis_law_query_text_limit: int = Field(default=1200, ge=200, le=5000)

    risk_red_threshold: float = 80.0
    risk_orange_threshold: float = 60.0
    risk_yellow_threshold: float = 40.0

    risk_case_count_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    risk_people_count_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_growth_rate_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_repeat_defendant_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_total_amount_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    risk_weight_case_count: float = Field(default=0.30, ge=0.0, le=1.0)
    risk_weight_people_count: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_weight_trend: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_weight_repeat_defendant: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_weight_total_amount: float = Field(default=0.10, ge=0.0, le=1.0)
    risk_case_count_cap: int = 20
    risk_total_amount_cap: float = 500000.0
    risk_people_count_cap: int = 50
    risk_growth_rate_cap: float = 1.0
    risk_repeat_defendant_rate_cap: float = 1.0

    alert_repeat_defendant_threshold_30d: int = 32
    alert_group_people_threshold: int = 10


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
