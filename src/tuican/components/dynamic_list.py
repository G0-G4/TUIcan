from collections.abc import Callable
from typing import Any

from .component import Component


class DynamicList:
    """Dynamic list helper for rendering a variable number of item rows.

    Each item is rendered via a user-provided factory function that returns
    a row of components. Ideal for CRUD interfaces where items are added and
    removed dynamically.

    Example:
        self.todos = DynamicList(item_factory=self._make_todo_row)
        self.todos.set_data([("Buy milk", False), ("Walk dog", True)])
        super().__init__(self.todos.components)

        def _make_todo_row(self, item, index):
            text, done = item
            cb = CheckBox(text, selected=done, on_change=self._make_toggle(index))
            return [cb]

        def get_layout(self):
            return self.todos.get_layout()
    """

    def __init__(
        self,
        item_factory: Callable[[Any, int], list[Component]],
    ):
        self._item_factory = item_factory
        self._data: list[Any] = []
        self._rows: list[list[Component]] = []
        self._all_components: list[Component] = []

    def set_data(self, data: list[Any]) -> None:
        self._data = list(data)
        self._rebuild()

    def add_item(self, item: Any) -> None:
        self._data.append(item)
        self._rebuild()

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self._data):
            del self._data[index]
            self._rebuild()

    def clear(self) -> None:
        self._data = []
        self._rebuild()

    def _rebuild(self) -> None:
        self._rows = []
        self._all_components = []
        for i, item in enumerate(self._data):
            row = self._item_factory(item, i)
            self._rows.append(row)
            self._all_components.extend(row)

    @property
    def data(self) -> list[Any]:
        return list(self._data)

    @property
    def components(self) -> list[Component]:
        return list(self._all_components)

    def get_layout(self) -> list[list[Component]]:
        return [list(row) for row in self._rows]
