import pytest

from app.tools import tool_registry
from app.tools.customer import search_customer


def test_search_customer_is_registered():
    assert tool_registry.has("search_customer")


def test_get_search_customer_tool():
    tool = tool_registry.get("search_customer")

    assert tool.name == "search_customer"
    assert tool.function is search_customer


def test_list_tools():
    tools = tool_registry.list_tools()

    names = [tool.name for tool in tools]

    assert "search_customer" in names


def test_unknown_tool_is_rejected():
    with pytest.raises(KeyError):
        tool_registry.get("does_not_exist")


def test_duplicate_tool_is_rejected():
    with pytest.raises(ValueError):
        tool_registry.register(
            name="search_customer",
            description="Duplicate tool",
            function=search_customer,
        )