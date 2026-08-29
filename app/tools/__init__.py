from app.tools.customer import search_customer
from app.tools.registry import ToolRegistry

tool_registry = ToolRegistry()

tool_registry.register(
    name='search_customer',
    description="Search customers belonging to the authenticated user by name, email, phone, or company.",
    function=search_customer,
)