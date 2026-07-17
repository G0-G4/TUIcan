import os
from typing import ClassVar

from dotenv import load_dotenv

from tuican.application import Application
from tuican.components import Button, Screen


class MyScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self):
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="click the button")

    def handle_click(self):
        self.message = "Hello world!"

    def get_layout(self):
        return [[self.button]]


load_dotenv()
token = os.getenv("token")
app = Application(token, {'start': MyScreen})
app.run()
