import dataclasses
import enum

import pytest

from tuican.errors import UserNotFoundError
from tuican.update import TuicanUpdate, UpdateKind, get_user_id


class TestUpdateKind:
    def test_is_enum(self):
        assert isinstance(UpdateKind, type) and issubclass(UpdateKind, enum.Enum)

    def test_members_present(self):
        assert UpdateKind.COMMAND in UpdateKind
        assert UpdateKind.CALLBACK in UpdateKind
        assert UpdateKind.MESSAGE in UpdateKind


class TestTuicanUpdateConstruction:
    def test_from_command_sets_kind(self):
        u = TuicanUpdate.from_command(
            user_id=1, chat_id=2, message_text="/start", message_id=10
        )
        assert u.kind is UpdateKind.COMMAND
        assert u.user_id == 1
        assert u.chat_id == 2
        assert u.message_text == "/start"
        assert u.message_id == 10
        assert u.callback_data is None

    def test_from_callback_sets_kind(self):
        u = TuicanUpdate.from_callback(
            user_id=3, chat_id=4, callback_data="cb:1", message_id=20
        )
        assert u.kind is UpdateKind.CALLBACK
        assert u.user_id == 3
        assert u.chat_id == 4
        assert u.callback_data == "cb:1"
        assert u.message_id == 20
        assert u.message_text is None

    def test_from_message_sets_kind(self):
        u = TuicanUpdate.from_message(
            user_id=5, chat_id=6, message_text="hello", message_id=30
        )
        assert u.kind is UpdateKind.MESSAGE
        assert u.user_id == 5
        assert u.chat_id == 6
        assert u.message_text == "hello"
        assert u.message_id == 30
        assert u.callback_data is None


class TestTuicanUpdateImmutability:
    def test_frozen(self):
        u = TuicanUpdate.from_command(
            user_id=1, chat_id=2, message_text="/start", message_id=10
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            u.user_id = 999  # type: ignore[misc]

    def test_has_slots(self):
        assert hasattr(TuicanUpdate, "__slots__")
        with pytest.raises(AttributeError):
            object.__getattribute__(
                TuicanUpdate.from_command(
                    user_id=1,
                    chat_id=2,
                    message_text="/start",
                    message_id=10,
                ),
                "__dict__",
            )


class TestGetUserId:
    def test_returns_user_id_when_present(self):
        u = TuicanUpdate.from_command(
            user_id=42, chat_id=2, message_text="/start", message_id=10
        )
        assert get_user_id(u) == 42

    def test_raises_when_user_id_is_none(self):
        u = TuicanUpdate(
            user_id=None,
            chat_id=2,
            callback_data="cb",
            message_text=None,
            message_id=10,
            kind=UpdateKind.CALLBACK,
        )
        with pytest.raises(UserNotFoundError):
            get_user_id(u)


class TestPackageReExports:
    def test_tuican_update_re_exported(self):
        import tuican

        assert hasattr(tuican, "TuicanUpdate")
        assert tuican.TuicanUpdate is TuicanUpdate

    def test_update_kind_re_exported(self):
        import tuican

        assert hasattr(tuican, "UpdateKind")
        assert tuican.UpdateKind is UpdateKind
