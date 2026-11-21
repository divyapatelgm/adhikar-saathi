from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys & LLM settings
    GEMINI_API_KEY: str = ""
    GNANI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"

    # Security
    ADMIN_PASSWORD: str = "change_this_admin_password_in_production"

    # App Modes
    DEMO_MODE: bool = True
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000"

    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    SQLITE_DB_PATH: Path = DATA_DIR / "adhikar_saathi.db"
    DATABASE_PATH: Path = DATA_DIR / "adhikar_saathi.db"
    RAW_DIR: Path = DATA_DIR / "raw"
    REJECTED_DIR: Path = DATA_DIR / "rejected"
    SAMPLES_DIR: Path = DATA_DIR / "samples"
    VERIFIED_SCHEMES_PATH: Path = DATA_DIR / "schemes_verified.json"
    EXTRACTED_SCHEMES_PATH: Path = DATA_DIR / "schemes_extracted.json"
    RIGHTS_KB_PATH: Path = DATA_DIR / "rights_kb.json"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

settings = Settings()
