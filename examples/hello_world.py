import os
from typing import ClassVar

from dotenv import load_dotenv

from tuican import Application
from tuican.components import Button, Input, Screen


class HelloScreen(Screen):
    """Simple screen demonstrating button counter and text input."""

    description: ClassVar[str] = "hello world"

    def __init__(self):
        self.counter = 0
        self.name = "World"

        self.count_btn = Button("Count", on_change=self.handle_count)
        self.name_input = Input[str](
            text="Name",
            validation_function=lambda x: x,
            on_change=self.handle_name,
            active_prompt="Enter your name: ",
        )

        super().__init__([self.count_btn, self.name_input], message=self._greeting())

    def _greeting(self) -> str:
        return f"Hello, {self.name}! Presses: {self.counter}"

    def handle_count(self):
        self.counter += 1
        self.message = self._greeting()

    def handle_name(self, component: Input):
        self.name = component.value or "World"
        self.message = self._greeting()

    def get_layout(self):
        return [
            [self.count_btn],
            [self.name_input],
        ]


load_dotenv()
token = os.getenv("token")
app = Application(token, {"start": HelloScreen})
app.run()
