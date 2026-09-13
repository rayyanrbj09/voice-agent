from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    DATABASE_URL: str

    #jwt 
    jwt_secret_key : str
    jwt_algorithm : str = 'HS256'
    access_token_expire_minutes : int = 30
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    anthropic_workspace_id: str | None = None
    agent_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 180.0
    ollama_keep_alive: str = "10m"
    ollama_context_length: int = 2048
    ollama_temperature: float = 0.1
    agent_max_tokens: int = 128
    agent_max_tool_rounds: int = 4
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "logs/voice-agent.log"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
