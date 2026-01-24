import os

from dotenv import load_dotenv

from src.tuican.application import Application
from src.tuican.components import Button, Screen

class MyScreen(Screen):
    def __init__(self):
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="click the button")

    def handle_click(self, update, context, callback_data, component):
        self.message = "Hello world!"

    def get_layout(self, update, context):
        return [[self.button.render(update, context)]]

load_dotenv()
token = os.getenv("token")
app = Application(token, MyScreen)
app.run()
