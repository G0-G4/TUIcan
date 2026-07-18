import json
import os
import tempfile
from pathlib import Path

from tuican.state_store import StateStore


class JsonFileStateStore(StateStore):
    """Persist user state to a local JSON file."""

    def __init__(self, filepath: str = "user_state.json"):
        self._filepath = Path(filepath).resolve()
        self._data: dict[str, str] = {}
        if self._filepath.exists():
            try:
                with open(self._filepath, encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to load state from %s, starting fresh: %s", self._filepath, exc
                )
                self._data = {}

    def _persist(self) -> None:
        try:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._filepath.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2)
                    f.flush()
                    os.fsync(fd)
                os.replace(tmp, self._filepath)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except OSError as exc:
            import logging
            logging.getLogger(__name__).exception("Failed to persist state to %s: %s", self._filepath, exc)

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
