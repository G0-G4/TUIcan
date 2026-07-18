from dataclasses import dataclass
from enum import IntEnum

from .errors import UserNotFoundError


class UpdateKind(IntEnum):
    COMMAND = 0
    CALLBACK = 1
    MESSAGE = 2


@dataclass(frozen=True, slots=True)
class TuicanUpdate:
    user_id: int | None
    chat_id: int | None
    callback_data: str | None = None
    message_text: str | None = None
    message_id: int | None = None
    kind: UpdateKind = UpdateKind.MESSAGE

    @classmethod
    def from_command(
        cls,
        user_id: int | None,
        chat_id: int | None,
        message_text: str | None,
        message_id: int | None,
    ) -> "TuicanUpdate":
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            message_text=message_text,
            message_id=message_id,
            kind=UpdateKind.COMMAND,
        )

    @classmethod
    def from_callback(
        cls,
        user_id: int | None,
        chat_id: int | None,
        callback_data: str | None,
        message_id: int | None,
    ) -> "TuicanUpdate":
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            callback_data=callback_data,
            message_id=message_id,
            kind=UpdateKind.CALLBACK,
        )

    @classmethod
    def from_message(
        cls,
        user_id: int | None,
        chat_id: int | None,
        message_text: str | None,
        message_id: int | None,
    ) -> "TuicanUpdate":
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            message_text=message_text,
            message_id=message_id,
            kind=UpdateKind.MESSAGE,
        )


def get_user_id(update: TuicanUpdate) -> int:
    if update.user_id is None:
        raise UserNotFoundError(update)
    return update.user_id
