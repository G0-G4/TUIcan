import pytest
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate
from tuican.components.toggle import Toggle


class TestToggle:
    def test_init_default_values(self):
        toggle = Toggle()
        assert toggle.on is False
        assert toggle.text == ""
        assert toggle.callback_data == toggle.component_id

    def test_init_custom_text(self):
        toggle = Toggle(text="Notifications")
        assert toggle.text == "Notifications"
        assert toggle._on_text == "Notifications"
        assert toggle._off_text == "Notifications"

    def test_init_separate_on_off_text(self):
        toggle = Toggle(on_text="Enabled", off_text="Disabled")
        assert toggle._on_text == "Enabled"
        assert toggle._off_text == "Disabled"

    def test_init_on_state(self):
        toggle = Toggle(on=True)
        assert toggle.on is True

    def test_text_setter_updates_display_text(self):
        toggle = Toggle(text="Old")
        toggle.text = "New"
        assert toggle.text == "New"
        assert toggle._on_text == "New"
        assert toggle._off_text == "New"

    def test_render_off(self, mock_screen):
        toggle = Toggle(text="Status", on=False, callback_data="tgl")
        toggle.parent_screen = mock_screen
        result = toggle.render()
        assert isinstance(result, KeyboardButton)
        assert result.text == "⬜ Status"
        assert result.callback_data == "tgl"

    def test_render_on(self, mock_screen):
        toggle = Toggle(text="Status", on=True, callback_data="tgl")
        toggle.parent_screen = mock_screen
        result = toggle.render()
        assert isinstance(result, KeyboardButton)
        assert result.text == "✅ Status"
        assert result.callback_data == "tgl"

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_screen):
        toggle = Toggle(text="Test", callback_data="correct")
        toggle.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_callback(
            user_id=123, chat_id=456, callback_data="wrong", message_id=1
        )
        result = await toggle.handle_callback()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_toggles(self, mock_screen):
        toggle = Toggle(text="Test", callback_data="match")
        toggle.parent_screen = mock_screen
        assert toggle.on is False

        mock_screen.update = TuicanUpdate.from_callback(
            user_id=123, chat_id=456, callback_data="match", message_id=1
        )
        result = await toggle.handle_callback()

        assert result is True
        assert toggle.on is True

    @pytest.mark.asyncio
    async def test_toggle_changes_state(self, mock_screen):
        toggle = Toggle(text="Test")
        toggle.parent_screen = mock_screen
        assert toggle.on is False

        await toggle.toggle()
        assert toggle.on is True

        await toggle.toggle()
        assert toggle.on is False

    @pytest.mark.asyncio
    async def test_toggle_triggers_on_change(self, mock_screen):
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        toggle = Toggle(text="Test", on_change=handler)
        toggle.parent_screen = mock_screen
        await toggle.toggle()

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_set_on_changes_state(self, mock_screen):
        toggle = Toggle(text="Test")
        toggle.parent_screen = mock_screen
        await toggle.set_on()
        assert toggle.on is True

    @pytest.mark.asyncio
    async def test_set_on_noop_when_already_on(self, mock_screen):
        from unittest.mock import AsyncMock
        handler = AsyncMock()
        toggle = Toggle(text="Test", on=True, on_change=handler)
        toggle.parent_screen = mock_screen
        await toggle.set_on()
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_off_changes_state(self, mock_screen):
        toggle = Toggle(text="Test", on=True)
        toggle.parent_screen = mock_screen
        await toggle.set_off()
        assert toggle.on is False

    @pytest.mark.asyncio
    async def test_set_off_noop_when_already_off(self, mock_screen):
        from unittest.mock import AsyncMock
        handler = AsyncMock()
        toggle = Toggle(text="Test", on=False, on_change=handler)
        toggle.parent_screen = mock_screen
        await toggle.set_off()
        handler.assert_not_called()

    def test_on_setter(self):
        toggle = Toggle(text="x")
        assert toggle.on is False
        toggle.on = True
        assert toggle.on is True
        toggle.on = False
        assert toggle.on is False

    def test_on_setter_does_not_fire_on_change(self, mock_screen):
        from unittest.mock import AsyncMock
        handler = AsyncMock()
        toggle = Toggle(text="x", on_change=handler)
        toggle.parent_screen = mock_screen
        toggle.on = True
        handler.assert_not_called()
        toggle.on = False
        handler.assert_not_called()
