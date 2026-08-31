from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Audit Log Service"
    api_prefix: str = ""
    database_url: str = "sqlite:///./audit.db"
    api_key: str = "super-secret-key-123"
    redaction_salt: str = "super-secret-salt-456"
    debug: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
