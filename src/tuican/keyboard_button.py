from dataclasses import dataclass

@dataclass
class KeyboardButton:
    text: str
    callback_data: str | None = None
