from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    session_id: str | None = Field(default=None, max_length=128)


class AgentChatResponse(BaseModel):
    session_id: str
    message: str
    tool_calls: list[str]
