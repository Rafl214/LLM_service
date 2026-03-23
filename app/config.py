from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default='LLM Service', alias='APP_NAME')

    api_key: str = Field(default='', alias='OPENAI_API_KEY')
    api_base_url: str | None = Field(default=None, alias='OPENAI_BASE_URL')
    model_name: str = Field(default='gpt-5.2', alias='OPENAI_MODEL')

    storage_dir: Path = Field(default=Path('storage'), alias='STORAGE_DIR')

    max_upload_size_mb: int = Field(default=30, alias='MAX_UPLOAD_SIZE_MB')
    max_parallel_requests: int = Field(default=5, alias='MAX_PARALLEL_REQUESTS')
    worker_count: int = Field(default=2, alias='WORKER_COUNT')
    request_timeout_seconds: int = Field(default=120, alias='REQUEST_TIMEOUT_SECONDS')

    allow_non_pdf_files: bool = Field(default=False, alias='ALLOW_NON_PDF_FILES')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        populate_by_name=True,
    )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def resolved_storage_dir(self) -> Path:
        return Path(self.storage_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()