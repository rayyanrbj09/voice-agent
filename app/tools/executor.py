from typing import Any

from sqlalchemy.orm import Session

from app.tools import tool_registry
from app.tools.registry import ToolRegistry


class ToolExecutionError(Exception):
    """Raised when a tool cannot be executed safely."""


def execute_tool(
    db: Session,
    user_id: int,
    tool_name: str,
    arguments: dict[str, Any],
    registry: ToolRegistry | None = None,
) -> Any:
    """
    Execute a registered tool on behalf of an authenticated user.

    The user_id comes from the authenticated backend context.
    It must not be supplied by the LLM.
    """

    try:
        tool = (registry or tool_registry).get(tool_name)
    except KeyError as exc:
        raise ToolExecutionError(
            f"Unknown tool: {tool_name}"
        ) from exc

    try:
        return tool.function(
            db=db,
            user_id=user_id,
            **arguments,
        )
    except TypeError as exc:
        raise ToolExecutionError(
            f"Invalid arguments for tool: {tool_name}"
        ) from exc
    except Exception as exc:
        raise ToolExecutionError(
            f"Tool execution failed: {tool_name}"
        ) from exc
