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
                 on_change: CallBack | None = None,
                 active_prompt: str = "Enter: "):
        """
        Initialize the Input component.

        Args:
            on_change: Callback function that will be called with the input value
            active_prompt: Prefix shown when input is active and accepting messages
        """
        super().__init__(component_id, callback_data, on_change)
        self._value = value
        self._text = text
        self._active = False
        self._validation_function = validation_function
        self._active_prompt = active_prompt

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

        await self.call_on_change(update, context)

        self._active = False
        if self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        return True

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if update.callback_query.data != self.callback_data:
            return False
        await self.toggle(update, context)
        return True

    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"{self._active_prompt if self.active else ''}{self._text}{self._value if self._value is not None else ''}",
            callback_data=self.callback_data
        )

    async def activate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activate the input to start accepting messages"""
        self._active = True
        self._value = None
        if self.parent_screen is not None:
            await self.parent_screen.set_focus(self, update, context)
        await self.call_on_change(update, context)

    async def deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deactivate the input to stop accepting messages"""
        self._active = False
        if self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        await self.call_on_change(update, context)

    async def toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._active = not self.active
        if self._active and self.parent_screen is not None:
            await self.parent_screen.set_focus(self, update, context)
        elif not self._active and self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        await self.call_on_change(update, context)

    def validate_input(self, text: str):
        if not self._validation_function:
            return text
        return self._validation_function(text)

    @property
    def value(self) -> T | None:
        """Get the current input value"""
        return self._value

    @value.setter
    def value(self, value: T) -> T | None:
        """Get the current input value"""
        self._value = value

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
