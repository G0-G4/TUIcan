import json
import os
from typing import Protocol


class StateStore(Protocol):
    """Protocol for persisting user command state across bot restarts."""

    async def load_all(self) -> dict[str, str]:
        """Load all persisted user commands. Keys are user_id as strings."""
        ...

    async def load(self, user_id: int) -> str | None:
        """Load the persisted command for a single user."""
        ...

    async def save(self, user_id: int, command: str) -> None:
        """Persist a user's current command."""
        ...

    async def delete(self, user_id: int) -> None:
        """Remove a user's persisted command."""
        ...


class InMemoryStateStore:
    """Default volatile state store. State is lost on restart."""

    def __init__(self):
        self._data: dict[int, str] = {}

    async def load_all(self) -> dict[str, str]:
        return {str(k): v for k, v in self._data.items()}

    async def load(self, user_id: int) -> str | None:
        return self._data.get(user_id)

    async def save(self, user_id: int, command: str) -> None:
        self._data[user_id] = command

    async def delete(self, user_id: int) -> None:
        self._data.pop(user_id, None)


class JsonFileStateStore:
    """Persist user state to a local JSON file."""

    def __init__(self, filepath: str = "user_state.json"):
        self._filepath = filepath
        self._data: dict[str, str] = {}
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                self._data = json.load(f)

    def _persist(self):
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    async def load_all(self) -> dict[str, str]:
        return dict(self._data)

    async def load(self, user_id: int) -> str | None:
        return self._data.get(str(user_id))

    async def save(self, user_id: int, command: str) -> None:
        self._data[str(user_id)] = command
        self._persist()

    async def delete(self, user_id: int) -> None:
        if self._data.pop(str(user_id), None) is not None:
            self._persist()
