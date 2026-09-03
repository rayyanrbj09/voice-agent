import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.agent.guardrails import validate_user_message
from app.agent.memory import ConversationMemory
from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import Settings
from app.tools.executor import ToolExecutionError, execute_tool
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ProviderResponse:
    content: list[dict[str, Any]]


class MessageProvider(Protocol):
    def create_message(self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ProviderResponse: ...


class AnthropicProvider:
    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install the 'anthropic' package to use the agent.") from exc
        headers = (
            {"anthropic-workspace-id": settings.anthropic_workspace_id}
            if settings.anthropic_workspace_id
            else None
        )
        self._client = Anthropic(
            api_key=settings.anthropic_api_key,
            default_headers=headers,
        )
        self._model = settings.anthropic_model
        self._max_tokens = settings.agent_max_tokens

    def create_message(self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ProviderResponse:
        response = self._client.messages.create(model=self._model, max_tokens=self._max_tokens, system=system, messages=messages, tools=tools)
        content: list[dict[str, Any]] = []
        for block in response.content:
            if block.type == "text":
                content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        return ProviderResponse(content=content)


class OllamaProvider:
    """Adapter for Ollama's local chat and tool-calling API."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=settings.ollama_timeout_seconds)
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._max_tokens = settings.agent_max_tokens

    def create_message(self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ProviderResponse:
        response = self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "messages": self._to_ollama_messages(system, messages),
                "tools": self._to_ollama_tools(tools),
                "options": {"num_predict": self._max_tokens},
                "stream": False,
            },
        )
        response.raise_for_status()
        message = response.json()["message"]
        content: list[dict[str, Any]] = []
        if text := message.get("content", ""):
            content.append({"type": "text", "text": text})
        for index, call in enumerate(message.get("tool_calls", [])):
            function = call["function"]
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            content.append({"type": "tool_use", "id": f"ollama-{index}", "name": function["name"], "input": arguments})
        return ProviderResponse(content=content)

    @staticmethod
    def _to_ollama_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]}} for tool in tools]

    @staticmethod
    def _to_ollama_messages(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = [{"role": "system", "content": system}]
        tool_names: dict[str, str] = {}
        for message in messages:
            content = message["content"]
            if isinstance(content, str):
                converted.append({"role": message["role"], "content": content})
                continue
            if message["role"] == "assistant":
                text = "\n".join(block["text"] for block in content if block["type"] == "text")
                tool_calls = []
                for block in content:
                    if block["type"] == "tool_use":
                        tool_names[block["id"]] = block["name"]
                        tool_calls.append({"function": {"name": block["name"], "arguments": block["input"]}})
                converted.append({"role": "assistant", "content": text, **({"tool_calls": tool_calls} if tool_calls else {})})
                continue
            for block in content:
                converted.append({"role": "tool", "tool_name": tool_names.get(block["tool_use_id"], "unknown"), "content": block["content"]})
        return converted


def create_provider(settings: Settings) -> MessageProvider:
    provider = settings.agent_provider.lower()
    if provider == "ollama":
        return OllamaProvider(settings)
    if provider == "anthropic":
        return AnthropicProvider(settings)
    raise RuntimeError(f"Unsupported agent provider: {settings.agent_provider}")


@dataclass(frozen=True)
class AgentResult:
    session_id: str
    message: str
    tool_calls: list[str]


class VoiceAgent:
    def __init__(self, provider: MessageProvider, registry: ToolRegistry, memory: ConversationMemory | None = None, max_tool_rounds: int = 4):
        self._provider = provider
        self._registry = registry
        self._memory = memory or ConversationMemory()
        self._max_tool_rounds = max_tool_rounds

    def respond(self, *, db: Session, user_id: int, message: str, session_id: str | None = None) -> AgentResult:
        session_id = session_id or str(uuid4())
        messages = self._memory.get(session_id)
        user_message = {"role": "user", "content": validate_user_message(message)}
        messages.append(user_message)
        tool_calls: list[str] = []

        for _ in range(self._max_tool_rounds + 1):
            response = self._provider.create_message(system=SYSTEM_PROMPT, messages=messages, tools=self._tool_specs())
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)
            requested_tools = [block for block in response.content if block["type"] == "tool_use"]
            if not requested_tools:
                text = "\n".join(block["text"] for block in response.content if block["type"] == "text").strip()
                self._memory.append(session_id, user_message)
                self._memory.append(session_id, assistant_message)
                return AgentResult(session_id=session_id, message=text or "I’m sorry, but I couldn’t generate a response.", tool_calls=tool_calls)
            if len(tool_calls) >= self._max_tool_rounds:
                raise RuntimeError("The agent exceeded the maximum number of tool calls.")
            results = []
            for tool_call in requested_tools:
                tool_calls.append(tool_call["name"])
                try:
                    value = execute_tool(db=db, user_id=user_id, tool_name=tool_call["name"], arguments=tool_call["input"], registry=self._registry)
                    results.append({"type": "tool_result", "tool_use_id": tool_call["id"], "content": self._serialize(value)})
                except ToolExecutionError as exc:
                    results.append({"type": "tool_result", "tool_use_id": tool_call["id"], "content": str(exc), "is_error": True})
            messages.append({"role": "user", "content": results})
        raise RuntimeError("The agent exceeded the maximum number of tool rounds.")

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [{"name": tool.name, "description": tool.description, "input_schema": tool.input_schema} for tool in self._registry.list_tools()]

    @staticmethod
    def _serialize(value: Any) -> str:
        def item(entry: Any) -> Any:
            if hasattr(entry, "__table__"):
                return {column.name: getattr(entry, column.name) for column in entry.__table__.columns}
            return entry
        return json.dumps([item(entry) for entry in value] if isinstance(value, list) else item(value), default=str)
