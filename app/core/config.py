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
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 60.0
    agent_max_tokens: int = 256
    agent_max_tool_rounds: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
