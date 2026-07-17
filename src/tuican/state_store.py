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
