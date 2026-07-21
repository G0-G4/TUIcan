import pytest
from tuican.components.dynamic_list import DynamicList
from tuican.components.button import Button
from tuican.components.label import Label


class TestDynamicList:
    def test_init_empty(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        assert dl.data == []
        assert dl.components == []
        assert dl.get_layout() == []

    def test_set_data(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        dl.set_data(["a", "b", "c"])
        assert dl.data == ["a", "b", "c"]
        assert len(dl.components) == 3
        assert len(dl.get_layout()) == 3

    def test_add_item(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        dl.set_data(["a"])
        dl.add_item("b")
        assert dl.data == ["a", "b"]
        assert len(dl.components) == 2

    def test_remove_item(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        dl.set_data(["a", "b", "c"])
        dl.remove_item(1)
        assert dl.data == ["a", "c"]
        assert len(dl.components) == 2

    def test_remove_item_out_of_bounds(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        dl.set_data(["a"])
        dl.remove_item(100)  # should not raise
        assert dl.data == ["a"]

    def test_clear(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        dl.set_data(["a", "b"])
        dl.clear()
        assert dl.data == []
        assert dl.components == []

    def test_factory_receives_index(self):
        indices = []

        def factory(item, idx):
            indices.append(idx)
            return [Label(str(item))]

        dl = DynamicList(item_factory=factory)
        dl.set_data(["a", "b"])
        assert indices == [0, 1]

    def test_multi_component_rows(self):
        def factory(item, idx):
            return [Label(str(item)), Button("Del")]

        dl = DynamicList(item_factory=factory)
        dl.set_data(["a", "b"])
        layout = dl.get_layout()
        assert len(layout) == 2
        assert len(layout[0]) == 2
        assert len(layout[1]) == 2
        assert len(dl.components) == 4

    def test_data_returns_copy(self):
        dl = DynamicList(item_factory=lambda item, idx: [Label(str(item))])
        original = ["a", "b"]
        dl.set_data(original)
        dl.data.append("c")
        assert dl._data == ["a", "b"]  # internal data unchanged
