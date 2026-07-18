import os
from typing import ClassVar

from dotenv import load_dotenv

from tuican import Application
from tuican.components import Button, CheckBox, Component, Input, Screen, ScreenGroup


class TodoListScreen(Screen):
    """Main screen showing the todo list with add/remove navigation."""

    def __init__(self, group: ScreenGroup):
        self.group = group
        self.todos: list[tuple[str, bool]] = []

        self.add_btn = Button("➕ Add todo", on_change=self.open_add_screen)
        self.clear_btn = Button("🗑 Clear done", on_change=self.clear_done)

        super().__init__([self.add_btn, self.clear_btn], message=self._list_message())

    def _list_message(self) -> str:
        if not self.todos:
            return "No todos yet. Add one!"
        lines = []
        for i, (text, done) in enumerate(self.todos, 1):
            mark = "✅" if done else "⬜"
            lines.append(f"{mark} {i}. {text}")
        return "Your todos:\n" + "\n".join(lines)

    def _sync_checkboxes(self):
        """Rebuild checkboxes to match current todo list."""
        for cb in getattr(self, "_checkboxes", []):
            self.delete_component(cb)

        self._checkboxes = []
        for idx, (text, done) in enumerate(self.todos):
            cb = CheckBox(
                text=text,
                selected=done,
                on_change=self._make_toggle(idx),
            )
            self.add_component(cb)
            self._checkboxes.append(cb)

    def _make_toggle(self, idx: int):
        def toggle(component: Component):
            if isinstance(component, CheckBox):
                self.todos[idx] = (self.todos[idx][0], component.selected)
                self.message = self._list_message()
        return toggle

    async def open_add_screen(self):
        screen = AddTodoScreen(self.group, self)
        await self.group.go_to_screen(self.update, screen)

    def clear_done(self):
        self.todos = [(text, done) for text, done in self.todos if not done]
        self._sync_checkboxes()
        self.message = self._list_message()

    def get_layout(self):
        self._sync_checkboxes()
        rows: list[list[Component]] = [[cb] for cb in getattr(self, "_checkboxes", [])]
        rows.append([self.add_btn, self.clear_btn])
        return rows


class AddTodoScreen(Screen):
    """Screen for adding a new todo via text input."""

    def __init__(self, group: ScreenGroup, list_screen: TodoListScreen):
        self.group = group
        self.list_screen = list_screen

        self.todo_input = Input[str](
            text="New todo",
            validation_function=lambda x: x,
            on_change=self.save_todo,
            active_prompt="Enter todo text: ",
        )
        self.back_btn = Button("⬅ Back", on_change=self.go_back)

        super().__init__([self.todo_input, self.back_btn], message="Add a new todo")

    async def save_todo(self, component: Component):
        if hasattr(component, "value") and component.value:
            self.list_screen.todos.append((str(component.value), False))
            self.list_screen.message = self.list_screen._list_message()
            await self.group.go_back(self.update)

    async def go_back(self):
        await self.group.go_back(self.update)

    def get_layout(self):
        return [
            [self.todo_input],
            [self.back_btn],
        ]


class TodoApp(ScreenGroup):
    """Root screen group managing navigation."""

    description: ClassVar[str] = "todo list"

    def __init__(self):
        self.list_screen = TodoListScreen(self)
        super().__init__(self.list_screen)


load_dotenv()
token = os.getenv("token")
app = Application(token, {"start": TodoApp}, transport="ptb")
app.run()
