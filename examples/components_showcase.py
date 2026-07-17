import os
from typing import ClassVar, Sequence

from dotenv import load_dotenv
from telegram import InlineKeyboardButton

from tuican import Application, get_user_id
from tuican.components import Button, CheckBox, Component, ExclusiveCheckBoxGroup, Hline, Input, Screen
from tuican.validation import positive_int


class ComponentsScreen(Screen):
    description: ClassVar[str] = "component show case"
    def __init__(self):
        group = ExclusiveCheckBoxGroup()
        self.check_box_1 = CheckBox(text="1", on_change=self.update_message, group=group)
        self.check_box_2 = CheckBox(text="2", on_change=self.update_message, group=group)
        self.button = Button(text="3", on_change=self.update_message)
        self.input = Input[int](text="возраст: ", value=123, on_change=self.update_message, validation_function=positive_int)
        super().__init__([self.check_box_1, self.check_box_2, self.button, self.input], message="show case")

    def update_message(self, component: Component):
        text = ""
        if isinstance(component, CheckBox) or isinstance(component, Button) or isinstance(component, Input):
            text = component.text
            self.message = "pressed " + text
        print(str(get_user_id(self.update)) + " pressed " + text)

    def get_layout(self) -> Sequence[Sequence[InlineKeyboardButton | Component]]:
        return [
            [self.check_box_1, self.check_box_2],
            [self.button],
            [self.input],
        ]


class SecondScreen(Screen):
    description: ClassVar[str] = 'second screen'
    def __init__(self):
        self.hline = Hline()
        super().__init__([self.hline], message="second screen")

    def get_layout(self) -> Sequence[Sequence[InlineKeyboardButton | Component]]:
        return [[self.hline]]


load_dotenv()
token = os.getenv("token")

app = Application(token, {'start': ComponentsScreen, 'second': SecondScreen})
app.run()
