import json
import os

from tuican.state_store import StateStore


class JsonFileStateStore(StateStore):
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
