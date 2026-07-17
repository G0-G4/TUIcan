import os
from typing import ClassVar

from dotenv import load_dotenv

from tuican import Application
from tuican.components import Button, Screen


class ButtonScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self):
        self.c = 0
        self.b = Button(text="my button", on_change=self.update_message)
        super().__init__([self.b], message="no presses")

    def update_message(self):
        self.c += 1
        self.message = "pressed " + str(self.c)

    def get_layout(self):
        return [[self.b]]


load_dotenv()
token = os.getenv("token")

app = Application(token, {'start': ButtonScreen})
app.run()
