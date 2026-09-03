from collections import defaultdict
from copy import deepcopy
from threading import RLock
from typing import Any


class ConversationMemory:
    """Bounded process-local conversation history for the initial agent release."""

    def __init__(self, max_messages: int = 30):
        self._max_messages = max_messages
        self._conversations: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._lock = RLock()

    def get(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._conversations[session_id])

    def append(self, session_id: str, message: dict[str, Any]) -> None:
        with self._lock:
            conversation = self._conversations[session_id]
            conversation.append(deepcopy(message))
            del conversation[:-self._max_messages]
