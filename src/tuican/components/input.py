from collections.abc import Callable

from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from .component import CallBack, MessageHandlingComponent


class Input[T](MessageHandlingComponent):

    def __init__(self,
                 validation_function: Callable[[str], T],
                 text: str = "",
                 value: T | None = None,
                 component_id: str | None = None,
                 callback_data: str = "",
                 on_change: CallBack | None = None):
        """
        Initialize the Input component.

        Args:
            on_change: Callback function that will be called with the input value
        """
        super().__init__(component_id, callback_data, on_change)
        self._value = value
        self._text = text
        self._active = False
        self._validation_function = validation_function

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle incoming text messages.

        Args:
            update: Telegram update object
            context: Telegram context object

        Returns:
            bool: True if message was handled, False otherwise
        """
        message = update.message
        if not message or not message.text:
            return False

        if not self._active:
            return False

        self._value = self.validate_input(message.text.strip())

        await self.call_on_change(update, context, str(self._value))

        self._active = False
        return True

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        if callback_data != self.callback_data:
            return False
        await self.toggle(update, context, callback_data)
        return True

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"{'Введите ' if self.active else ''}{self._text}{self._value}",
            callback_data=self.callback_data
        )

    async def activate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str | None):
        """Activate the input to start accepting messages"""
        self._active = True
        self._value = None
        await self.call_on_change(update, context, callback_data)

    async def deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str | None):
        """Deactivate the input to stop accepting messages"""
        self._active = False
        await self.call_on_change(update, context, callback_data)

    async def toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str | None):
        self._active = not self.active
        await self.call_on_change(update, context, callback_data)

    def validate_input(self, text: str):
        if not self._validation_function:
            return text
        return self._validation_function(text)

    @property
    def value(self) -> str | None:
        """Get the current input value"""
        return self._value

    @property
    def text(self) -> str | None:
        """Get the current input value"""
        return self._text

    @text.setter
    def text(self, text) -> str | None:
        """Get the current input value"""
        self._text = text

    @property
    def active(self) -> bool:
        """Check if input is currently active and accepting messages"""
        return self._active
