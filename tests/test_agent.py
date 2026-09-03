import pytest
from copy import deepcopy
from types import SimpleNamespace
import sys

from app.agent.guardrails import GuardrailViolation
from app.agent.orchestrator import AnthropicProvider, OllamaProvider, ProviderResponse, VoiceAgent, create_provider
from app.core.config import Settings
from app.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def create_message(self, *, system, messages, tools):
        self.requests.append({"system": system, "messages": deepcopy(messages), "tools": deepcopy(tools)})
        return next(self.responses)


def test_anthropic_provider_sends_workspace_header_for_identity_linked_keys(monkeypatch):
    created = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            created.update(kwargs)

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))
    settings = Settings.model_construct(
        anthropic_api_key="test-key",
        anthropic_workspace_id="workspace-123",
        anthropic_model="test-model",
        agent_max_tokens=1,
    )

    AnthropicProvider(settings)

    assert created["default_headers"] == {"anthropic-workspace-id": "workspace-123"}


def test_ollama_provider_uses_local_chat_api_and_normalizes_tool_calls():
    request = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "Searching.", "tool_calls": [{"function": {"name": "lookup", "arguments": {"query": "Rayyan"}}}]}}

    class FakeClient:
        def post(self, url, json):
            request["url"] = url
            request["body"] = json
            return FakeResponse()

    settings = Settings.model_construct(
        ollama_base_url="http://localhost:11434/",
        ollama_model="llama3.1:8b",
        ollama_timeout_seconds=1,
        agent_max_tokens=32,
    )
    provider = OllamaProvider(settings, client=FakeClient())
    response = provider.create_message(
        system="System prompt",
        messages=[{"role": "user", "content": "Find Rayyan"}],
        tools=[{"name": "lookup", "description": "Looks up values.", "input_schema": {"type": "object"}}],
    )

    assert request["url"] == "http://localhost:11434/api/chat"
    assert request["body"]["model"] == "llama3.1:8b"
    assert request["body"]["options"] == {"num_predict": 32}
    assert request["body"]["messages"][0] == {"role": "system", "content": "System prompt"}
    assert response.content == [
        {"type": "text", "text": "Searching."},
        {"type": "tool_use", "id": "ollama-0", "name": "lookup", "input": {"query": "Rayyan"}},
    ]


def test_ollama_is_the_default_provider():
    settings = Settings.model_construct(agent_provider="ollama", ollama_base_url="http://localhost:11434", ollama_model="llama3.1:8b", ollama_timeout_seconds=1)
    assert isinstance(create_provider(settings), OllamaProvider)


def test_agent_returns_provider_text_and_remembers_the_conversation():
    provider = FakeProvider([
        ProviderResponse(content=[{"type": "text", "text": "Hello."}]),
        ProviderResponse(content=[{"type": "text", "text": "Welcome back."}]),
    ])
    agent = VoiceAgent(provider, ToolRegistry())

    first = agent.respond(db=None, user_id=1, message="Hi")
    second = agent.respond(db=None, user_id=1, message="Continue", session_id=first.session_id)

    assert first.message == "Hello."
    assert second.message == "Welcome back."
    assert provider.requests[1]["messages"] == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello."}]},
        {"role": "user", "content": "Continue"},
    ]


def test_agent_executes_tool_and_returns_the_final_response():
    registry = ToolRegistry()
    registry.register(
        name="lookup",
        description="Looks up a value.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        function=lambda db, user_id, query: {"owner": user_id, "query": query},
    )
    provider = FakeProvider([
        ProviderResponse(content=[{"type": "tool_use", "id": "tool-1", "name": "lookup", "input": {"query": "Rayyan"}}]),
        ProviderResponse(content=[{"type": "text", "text": "I found Rayyan."}]),
    ])
    result = VoiceAgent(provider, registry).respond(db=None, user_id=42, message="Find Rayyan")

    assert result.message == "I found Rayyan."
    assert result.tool_calls == ["lookup"]
    tool_result = provider.requests[1]["messages"][-1]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["content"] == '{"owner": 42, "query": "Rayyan"}'


def test_agent_rejects_blank_messages_without_calling_provider():
    provider = FakeProvider([])
    with pytest.raises(GuardrailViolation, match="must not be empty"):
        VoiceAgent(provider, ToolRegistry()).respond(db=None, user_id=1, message="  ")
    assert provider.requests == []
