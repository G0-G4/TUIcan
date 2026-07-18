import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tuican.stores.in_memory import InMemoryStateStore
from tuican.stores.json_file import JsonFileStateStore


class TestInMemoryStateStore:
    @pytest.fixture
    def store(self):
        return InMemoryStateStore()

    @pytest.mark.asyncio
    async def test_save_load_round_trip(self, store):
        """save followed by load should return the stored command."""
        await store.save(user_id=1, command="start")
        result = await store.load(user_id=1)
        assert result == "start"

    @pytest.mark.asyncio
    async def test_load_missing_returns_none(self, store):
        """load for an unknown user_id should return None."""
        result = await store.load(user_id=999)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_entry(self, store):
        """delete should remove the user's command."""
        await store.save(user_id=1, command="start")
        await store.delete(user_id=1)
        result = await store.load(user_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_missing_no_error(self, store):
        """delete for an unknown user_id should not raise."""
        await store.delete(user_id=999)

    @pytest.mark.asyncio
    async def test_load_all_returns_all(self, store):
        """load_all should return every saved entry with string keys."""
        await store.save(user_id=1, command="start")
        await store.save(user_id=2, command="help")
        result = await store.load_all()
        assert result == {"1": "start", "2": "help"}

    @pytest.mark.asyncio
    async def test_overwrite_existing(self, store):
        """save with the same user_id should overwrite the previous command."""
        await store.save(user_id=1, command="start")
        await store.save(user_id=1, command="help")
        result = await store.load(user_id=1)
        assert result == "help"


class TestJsonFileStateStore:
    @pytest.fixture
    def temp_file(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def store(self, temp_file):
        return JsonFileStateStore(filepath=temp_file)

    @pytest.mark.asyncio
    async def test_save_load_round_trip(self, store, temp_file):
        """save followed by load should return the stored command."""
        await store.save(user_id=1, command="start")
        result = await store.load(user_id=1)
        assert result == "start"

    @pytest.mark.asyncio
    async def test_load_missing_returns_none(self, store):
        """load for an unknown user_id should return None."""
        result = await store.load(user_id=999)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_entry(self, store, temp_file):
        """delete should remove the user's command and persist."""
        await store.save(user_id=1, command="start")
        await store.delete(user_id=1)
        result = await store.load(user_id=1)
        assert result is None
        with open(temp_file, encoding="utf-8") as f:
            data = json.load(f)
        assert "1" not in data

    @pytest.mark.asyncio
    async def test_delete_missing_no_error(self, store):
        """delete for an unknown user_id should not raise."""
        await store.delete(user_id=999)

    @pytest.mark.asyncio
    async def test_load_all_returns_all(self, store):
        """load_all should return every saved entry."""
        await store.save(user_id=1, command="start")
        await store.save(user_id=2, command="help")
        result = await store.load_all()
        assert result == {"1": "start", "2": "help"}

    @pytest.mark.asyncio
    async def test_overwrite_existing(self, store):
        """save with the same user_id should overwrite the previous command."""
        await store.save(user_id=1, command="start")
        await store.save(user_id=1, command="help")
        result = await store.load(user_id=1)
        assert result == "help"

    @pytest.mark.asyncio
    async def test_data_survives_reinstantiation(self, temp_file):
        """Data written by one store instance should be readable by another."""
        store1 = JsonFileStateStore(filepath=temp_file)
        await store1.save(user_id=1, command="start")
        store2 = JsonFileStateStore(filepath=temp_file)
        result = await store2.load(user_id=1)
        assert result == "start"

    def test_missing_file_starts_fresh(self, temp_file):
        """When the file does not exist, the store should start with empty data."""
        os.unlink(temp_file)
        store = JsonFileStateStore(filepath=temp_file)
        assert store._data == {}

    def test_corrupted_file_starts_fresh(self, temp_file):
        """When the file contains invalid JSON, the store should start fresh and log a warning."""
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("not json")
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            store = JsonFileStateStore(filepath=temp_file)
            assert store._data == {}
            mock_logger.warning.assert_called_once()
            assert "Failed to load state" in mock_logger.warning.call_args.args[0]

    @pytest.mark.asyncio
    async def test_atomic_write(self, store, temp_file):
        """_persist should write to a temp file and atomically replace the target."""
        await store.save(user_id=1, command="start")
        assert Path(temp_file).exists()
        with open(temp_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data == {"1": "start"}

    @pytest.mark.asyncio
    async def test_persist_error_handling(self, store, temp_file):
        """_persist should log an exception when writing fails and not raise."""
        with patch("tuican.stores.json_file.os.fdopen", side_effect=OSError("disk full")):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                await store.save(user_id=1, command="start")
                mock_logger.exception.assert_called_once()
                assert "Failed to persist state" in mock_logger.exception.call_args.args[0]

    def test_path_validation_resolves(self, temp_file):
        """The filepath should be resolved to an absolute Path."""
        store = JsonFileStateStore(filepath=temp_file)
        assert store._filepath.is_absolute()
        assert store._filepath == Path(temp_file).resolve()

    @pytest.mark.asyncio
    async def test_persist_creates_parent_directories(self):
        """_persist should create parent directories if they do not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "a" / "b" / "state.json"
            store = JsonFileStateStore(filepath=str(nested))
            await store.save(user_id=1, command="start")
            assert nested.exists()
            with open(nested, encoding="utf-8") as f:
                data = json.load(f)
            assert data == {"1": "start"}
