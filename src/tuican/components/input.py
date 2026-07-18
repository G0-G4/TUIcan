from collections.abc import Callable

from ..keyboard_button import KeyboardButton
from .component import CallBack, MessageHandlingComponent


class Input[T](MessageHandlingComponent):

    def __init__(self,
                 validation_function: Callable[[str], T],
                 text: str = "",
                 value: T | None = None,
                 component_id: str | None = None,
                 callback_data: str | None = None,
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

    async def handle_message(self) -> bool:
        """
        Handle incoming text messages.

        Returns:
            bool: True if message was handled, False otherwise
        """
        update = self.update
        if not update or update.message_text is None:
            return False

        if not self._active:
            return False

        self._value = self.validate_input(update.message_text.strip())

        await self.call_on_change()

        self._active = False
        if self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        return True

    async def handle_callback(self) -> bool:
        update = self.update
        if update is None or update.callback_data is None or update.callback_data != self.callback_data:
            return False
        await self.toggle()
        return True

    def render(self) -> KeyboardButton:
        if self.active:
            text = f"{self._active_prompt}{self._value if self._value is not None else ''}"
        else:
            if self._value is not None and self._text:
                text = f"{self._text}: {self._value}"
            elif self._value is not None:
                text = str(self._value)
            else:
                text = self._text
        return KeyboardButton(text=text, callback_data=self.callback_data)

    async def activate(self) -> None:
        """Activate the input to start accepting messages"""
        self._active = True
        self._value = None
        if self.parent_screen is not None:
            await self.parent_screen.set_focus(self)
        await self.call_on_change()

    async def deactivate(self) -> None:
        """Deactivate the input to stop accepting messages"""
        self._active = False
        if self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        await self.call_on_change()

    async def toggle(self) -> None:
        self._active = not self.active
        if self._active and self.parent_screen is not None:
            await self.parent_screen.set_focus(self)
        elif not self._active and self.parent_screen is not None:
            self.parent_screen.clear_active_message_component(self)
        await self.call_on_change()

    def validate_input(self, text: str) -> T:
        return self._validation_function(text)

    @property
    def value(self) -> T | None:
        """Get the current input value"""
        return self._value

    @value.setter
    def value(self, value: T | None) -> None:
        """Set the current input value"""
        self._value = value

    @property
    def text(self) -> str:
        """Get the current input text"""
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        """Set the current input text"""
        self._text = text

    @property
    def active(self) -> bool:
        """Check if input is currently active and accepting messages"""
        return self._active
