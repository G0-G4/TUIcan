import pytest
from unittest.mock import MagicMock, AsyncMock

from tuican.keyboard_button import KeyboardButton
from tuican.components.label import Label
from tuican.components.button import Button
from tuican.components.screen import Screen


class TestLabel:
    def test_text_property(self):
        """Label should store and expose text"""
        label = Label("hi")
        assert label.text == "hi"

    def test_render_returns_keyboard_button(self):
        """render() should return a KeyboardButton with correct text and callback_data"""
        label = Label("hi")
        result = label.render()

        assert isinstance(result, KeyboardButton)
        assert result.text == "hi"
        assert result.callback_data is not None
        assert result.callback_data.startswith("label_")

    @pytest.mark.asyncio
    async def test_handle_callback_returns_false(self):
        """handle_callback should always return False (non-interactive)"""
        label = Label("x")
        result = await label.handle_callback()
        assert result is False

    def test_multiple_labels_no_collision(self):
        """Two Labels with same text should register into a Screen without collision"""
        label_a = Label("same")
        label_b = Label("same")

        class LabelScreen(Screen):
            def __init__(self):
                self.label_a = label_a
                self.label_b = label_b
                super().__init__([self.label_a, self.label_b], message="test")

            def get_layout(self):
                return [[self.label_a, self.label_b]]

        screen = LabelScreen()
        assert label_a.callback_data != label_b.callback_data
        assert label_a.callback_data in screen._callback_map
        assert label_b.callback_data in screen._callback_map

    def test_text_setter(self):
        """Label text should be changeable via setter"""
        label = Label("old")
        label.text = "new"
        assert label.text == "new"

    @pytest.mark.asyncio
    async def test_display_round_trip(self):
        """Screen.display() should render Label alongside Button via backend"""
        label = Label("title")
        button = Button("go", callback_data="go_cb")

        class MixedScreen(Screen):
            def __init__(self):
                self.label = label
                self.button = button
                super().__init__([self.label, self.button], message="msg")

            def get_layout(self):
                return [[self.label, self.button]]

        backend = MagicMock()
        backend.send_keyboard_message = AsyncMock()

        screen = MixedScreen()
        screen.backend = backend

        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock()
        context = MagicMock()

        await screen.display(update, context)

        backend.send_keyboard_message.assert_awaited_once()
        call_args = backend.send_keyboard_message.await_args
        _target_update, _ctx, text, keyboard_markup = call_args.args

        assert text == "msg"
        assert len(keyboard_markup) == 1
        row = keyboard_markup[0]
        assert len(row) == 2
        assert row[0].text == "title"
        assert row[0].callback_data.startswith("label_")
        assert row[1].text == "go"
        assert row[1].callback_data == "go_cb"
