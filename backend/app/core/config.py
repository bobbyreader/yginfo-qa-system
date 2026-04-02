import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取backend目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database - PostgreSQL (use Supabase or similar for production)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./yg_knowledge.db",
        description="数据库连接URL，支持postgresql+asyncpg://或sqlite+aiosqlite:///",
    )

    # Pinecone
    pinecone_api_key: str = Field(default="", description="Pinecone API Key")
    pinecone_environment: str = Field(default="us-east-1", description="Pinecone环境")
    pinecone_namespace: str = Field(default="", description="Pinecone命名空间")

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API 中转地址")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI模型")

    # App
    app_name: str = Field(default="YG智能知识库问答系统", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
