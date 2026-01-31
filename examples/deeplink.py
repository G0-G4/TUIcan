import os
from mimetypes import init
from typing import ClassVar

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from src.tuican.application import Application
from src.tuican.components import Button, Screen
from tuican.components import ScreenGroup

'''
open https://t.me/<bot name>?start=123
and see the message from bot on accept
'''


class MyScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self, group: ScreenGroup):
        self.group = group
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="click the button")

    def handle_click(self, update, context, callback_data, component):
        self.message = "Hello world!"

    async def command_handler(self, args: list[str], update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(args) > 1:
            screen = DeepLinkScreen(self.group, args[1])
            await self.group.go_to_screen(update, context, screen)


    async def get_layout(self, update, context):
        return [[self.button.render(update, context)]]

class DeepLinkScreen(Screen):
    description: ClassVar[str] = 'main screen'
    def __init__(self, group: ScreenGroup, arg):
        self.group = group
        self.arg = arg
        self.action = Button("✅ perform action", on_change=self.handle_action)
        self.cancel = Button("❌ cancel", on_change=self.handle_cancel)
        super().__init__([self.action, self.cancel], message="perform action?")

    async def handle_action(self, update, context, callback_data, component):
        await self.send_message(update, context, f"action performed with argument {self.arg}")
        await self.group.go_home(update, context)

    async def handle_cancel(self, update, context, callback_data, component):
        await self.group.go_home(update, context)

    async def get_layout(self, update, context):
        return [[self.action.render(update, context), self.cancel.render(update, context)]]

class Grp(ScreenGroup):
    description: ClassVar[str] = "deep link example"
    def __init__(self):
        main = MyScreen(self)
        super().__init__(main)

load_dotenv()
token = os.getenv("token")
app = Application(token, {'start': Grp})
app.run()
