import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.metrics import record_tool_execution
from app.tools import tool_registry
from app.tools.registry import ToolRegistry


class ToolExecutionError(Exception):
    """Raised when a tool cannot be executed safely."""


logger = logging.getLogger(__name__)


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
        record_tool_execution(tool_name, "error")
        raise ToolExecutionError(
            f"Unknown tool: {tool_name}"
        ) from exc

    missing = [
        field for field in (tool.input_schema or {}).get("required", []) if field not in arguments
    ]
    if missing:
        record_tool_execution(tool_name, "error")
        if "customer_id" in missing:
            raise ToolExecutionError(
                f"Invalid arguments for tool {tool_name}: customer_id is required. Please search for the customer first and use the resolved customer_id before calling this tool."
            )
        raise ToolExecutionError(
            f"Invalid arguments for tool {tool_name}: missing required arguments: {', '.join(missing)}."
        )

    try:
        logger.info("Executing tool tool=%s user_id=%s", tool_name, user_id)
        result = tool.function(
            db=db,
            user_id=user_id,
            **arguments,
        )
        record_tool_execution(tool_name, "success")
        return result
    except TypeError as exc:
        record_tool_execution(tool_name, "error")
        raise ToolExecutionError(
            f"Invalid arguments for tool {tool_name}: {exc}"
        ) from exc
    except ValueError as exc:
        record_tool_execution(tool_name, "error")
        raise ToolExecutionError(
            f"Tool {tool_name} could not complete: {exc}"
        ) from exc
    except Exception as exc:
        record_tool_execution(tool_name, "error")
        logger.exception("Tool failed tool=%s user_id=%s", tool_name, user_id)
        raise ToolExecutionError(
            f"Tool execution failed: {tool_name}: {exc}"
        ) from exc
