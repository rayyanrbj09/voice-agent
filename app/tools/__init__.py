from app.tools.customer import search_customer
from app.tools.appointments import book_appointment, cancel_appointment, list_appointments
from app.tools.orders import create_order, list_orders
from app.tools.registry import ToolRegistry
from app.tools.support import create_support_ticket, list_support_tickets, update_support_ticket

tool_registry = ToolRegistry()

tool_registry.register(
    name='search_customer',
    description="Search customers belonging to the authenticated user by name, email, phone, or company.",
    function=search_customer,
    input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False},
)

tool_registry.register(
    name="book_appointment",
    description="Book an appointment for one of the authenticated user's customers.",
    function=book_appointment,
    input_schema={"type": "object", "properties": {"customer_id": {"type": "integer"}, "starts_at": {"type": "string", "description": "ISO-8601 datetime"}, "duration_minutes": {"type": "integer", "minimum": 1}, "notes": {"type": ["string", "null"]}}, "required": ["customer_id", "starts_at"], "additionalProperties": False},
)
tool_registry.register(
    name="list_appointments",
    description="List appointments belonging to the authenticated user, optionally filtered by status.",
    function=list_appointments,
    input_schema={"type": "object", "properties": {"status": {"type": "string"}}, "additionalProperties": False},
)
tool_registry.register(
    name="cancel_appointment",
    description="Cancel an appointment belonging to the authenticated user.",
    function=cancel_appointment,
    input_schema={"type": "object", "properties": {"appointment_id": {"type": "integer"}}, "required": ["appointment_id"], "additionalProperties": False},
)
tool_registry.register(
    name="create_order",
    description="Create an order for one of the authenticated user's customers.",
    function=create_order,
    input_schema={"type": "object", "properties": {"customer_id": {"type": "integer"}, "order_number": {"type": "string"}, "description": {"type": "string"}, "total_amount": {"type": "number", "minimum": 0}, "status": {"type": "string"}}, "required": ["customer_id", "order_number", "description"], "additionalProperties": False},
)
tool_registry.register(
    name="list_orders",
    description="List orders belonging to the authenticated user, optionally filtered by status.",
    function=list_orders,
    input_schema={"type": "object", "properties": {"status": {"type": "string"}}, "additionalProperties": False},
)
tool_registry.register(
    name="create_support_ticket",
    description="Create a support ticket for one of the authenticated user's customers.",
    function=create_support_ticket,
    input_schema={"type": "object", "properties": {"customer_id": {"type": "integer"}, "subject": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string"}}, "required": ["customer_id", "subject", "description"], "additionalProperties": False},
)
tool_registry.register(
    name="list_support_tickets",
    description="List support tickets belonging to the authenticated user, optionally filtered by status.",
    function=list_support_tickets,
    input_schema={"type": "object", "properties": {"status": {"type": "string"}}, "additionalProperties": False},
)
tool_registry.register(
    name="update_support_ticket",
    description="Update the status or priority of an authenticated user's support ticket.",
    function=update_support_ticket,
    input_schema={"type": "object", "properties": {"ticket_id": {"type": "integer"}, "status": {"type": "string"}, "priority": {"type": "string"}}, "required": ["ticket_id"], "additionalProperties": False},
)
