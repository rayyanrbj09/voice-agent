class GuardrailViolation(ValueError):
    """Raised when a message is unsuitable for the agent runtime."""


MAX_MESSAGE_LENGTH = 4_000


def validate_user_message(message: str) -> str:
    normalized = message.strip()
    if not normalized:
        raise GuardrailViolation("Message must not be empty.")
    if len(normalized) > MAX_MESSAGE_LENGTH:
        raise GuardrailViolation(f"Message must be at most {MAX_MESSAGE_LENGTH} characters.")
    return normalized
