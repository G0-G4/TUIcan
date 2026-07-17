from tuican.state_store import StateStore


class InMemoryStateStore(StateStore):
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
