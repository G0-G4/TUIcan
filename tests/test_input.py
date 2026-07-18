import pytest
from unittest.mock import AsyncMock, MagicMock
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate
from tuican.components.input import Input


class TestInput:
    def test_init_default_values(self):
        """Input should initialize with default values"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.text == ""
        assert inp.value is None
        assert inp.active is False
        assert inp.callback_data == inp.component_id

    def test_init_with_callback_data(self):
        """Input should use explicit callback_data"""
        inp = Input[str](validation_function=lambda x: x, callback_data="custom")
        assert inp.callback_data == "custom"

    def test_text_setter(self):
        """Input text should be changeable"""
        inp = Input[str](validation_function=lambda x: x, text="Old")
        inp.text = "New"
        assert inp.text == "New"

    def test_value_setter(self):
        """Input value should be changeable"""
        inp = Input[str](validation_function=lambda x: x)
        inp.value = "test"
        assert inp.value == "test"

    def test_render_inactive(self, mock_screen):
        """render() should show inactive state without active prompt"""
        inp = Input[str](validation_function=lambda x: x, text="Name")
        inp.parent_screen = mock_screen
        result = inp.render()

        assert isinstance(result, KeyboardButton)
        assert "Name" == result.text
        assert "Enter:" not in result.text

    def test_render_active(self, mock_screen):
        """render() should show active state with default English prompt and value"""
        inp = Input[str](validation_function=lambda x: x, text="Name", value="John")
        inp._active = True
        inp.parent_screen = mock_screen
        result = inp.render()

        assert isinstance(result, KeyboardButton)
        assert "Enter:" in result.text
        assert "John" in result.text
        assert "Name" not in result.text

    def test_render_inactive_with_value(self, mock_screen):
        """render() should show label and value when inactive"""
        inp = Input[str](validation_function=lambda x: x, text="Name", value="John")
        inp.parent_screen = mock_screen
        result = inp.render()

        assert isinstance(result, KeyboardButton)
        assert "Name: John" == result.text

    def test_render_with_value(self, mock_screen):
        """render() should display label and current value separated by colon"""
        inp = Input[int](validation_function=int, text="Age", value=25)
        inp.parent_screen = mock_screen
        result = inp.render()

        assert isinstance(result, KeyboardButton)
        assert "Age: 25" == result.text

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_screen):
        """handle_callback should return False when callback_data doesn't match"""
        inp = Input[str](validation_function=lambda x: x, callback_data="correct")
        inp.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_callback(
            user_id=123, chat_id=456, callback_data="wrong", message_id=1
        )
        result = await inp.handle_callback()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_activates(self, mock_screen):
        """handle_callback should activate input when callback_data matches"""
        inp = Input[str](validation_function=lambda x: x, callback_data="match")
        inp.parent_screen = mock_screen
        assert inp.active is False

        mock_screen.update = TuicanUpdate.from_callback(
            user_id=123, chat_id=456, callback_data="match", message_id=1
        )
        result = await inp.handle_callback()

        assert result is True
        assert inp.active is True

    @pytest.mark.asyncio
    async def test_activate_sets_active(self, mock_screen):
        """activate() should set active to True"""
        inp = Input[str](validation_function=lambda x: x)
        inp.parent_screen = mock_screen
        assert inp.active is False

        await inp.activate()
        assert inp.active is True

    @pytest.mark.asyncio
    async def test_deactivate_sets_inactive(self, mock_screen):
        """deactivate() should set active to False"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True
        inp.parent_screen = mock_screen

        await inp.deactivate()
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_toggle_flips_state(self, mock_screen):
        """toggle() should flip active state"""
        inp = Input[str](validation_function=lambda x: x)
        inp.parent_screen = mock_screen
        assert inp.active is False

        await inp.toggle()
        assert inp.active is True

        await inp.toggle()
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_handle_message_when_inactive(self, mock_screen):
        """handle_message should return False when input is inactive"""
        inp = Input[str](validation_function=lambda x: x)
        inp.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_message(
            user_id=123, chat_id=456, message_text="hello", message_id=1
        )

        result = await inp.handle_message()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_message_no_text(self, mock_screen):
        """handle_message should return False when message has no text"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True
        inp.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_message(
            user_id=123, chat_id=456, message_text=None, message_id=1
        )

        result = await inp.handle_message()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_message_validates_and_sets_value(self, mock_screen):
        """handle_message should validate input and set value"""
        inp = Input[int](validation_function=int, value=None)
        inp._active = True
        inp.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_message(
            user_id=123, chat_id=456, message_text="42", message_id=1
        )

        result = await inp.handle_message()

        assert result is True
        assert inp.value == 42
        assert inp.active is False

    @pytest.mark.asyncio
    async def test_handle_message_triggers_on_change(self, mock_screen):
        """handle_message should trigger on_change; handler reads value from component"""
        handler_called = False
        received_component = None

        async def handler(component):
            nonlocal handler_called, received_component
            handler_called = True
            received_component = component

        inp = Input[int](validation_function=int, on_change=handler)
        inp._active = True
        inp.parent_screen = mock_screen
        mock_screen.update = TuicanUpdate.from_message(
            user_id=123, chat_id=456, message_text="42", message_id=1
        )

        await inp.handle_message()

        assert handler_called is True
        assert received_component is inp
        assert received_component.value == 42

    def test_validate_input_with_function(self):
        """validate_input should apply validation function"""
        inp = Input[int](validation_function=int)
        result = inp.validate_input("42")
        assert result == 42

    def test_validate_input_without_function(self):
        """validate_input should return raw text when no function provided"""
        inp = Input[str](validation_function=lambda x: x)
        result = inp.validate_input("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_activate_calls_set_focus_on_parent_screen(self, mock_screen):
        """activate() should call parent_screen.set_focus to enforce single active input"""
        inp = Input[str](validation_function=lambda x: x)
        mock_screen.set_focus = AsyncMock()
        inp.parent_screen = mock_screen

        await inp.activate()

        assert inp.active is True
        mock_screen.set_focus.assert_awaited_once_with(inp)

    @pytest.mark.asyncio
    async def test_toggle_on_calls_set_focus_on_parent_screen(self, mock_screen):
        """toggle() turning on should call parent_screen.set_focus"""
        inp = Input[str](validation_function=lambda x: x)
        mock_screen.set_focus = AsyncMock()
        inp.parent_screen = mock_screen

        await inp.toggle()

        assert inp.active is True
        mock_screen.set_focus.assert_awaited_once_with(inp)

    @pytest.mark.asyncio
    async def test_toggle_off_does_not_call_set_focus(self, mock_screen):
        """toggle() turning off should not call parent_screen.set_focus"""
        inp = Input[str](validation_function=lambda x: x)
        inp._active = True
        mock_screen.set_focus = MagicMock()
        inp.parent_screen = mock_screen

        await inp.toggle()

        assert inp.active is False
        mock_screen.set_focus.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_without_parent_screen_does_not_raise(self):
        """activate() should work when parent_screen is None (isolated component)"""
        inp = Input[str](validation_function=lambda x: x)
        assert inp.parent_screen is None

        await inp.activate()
        assert inp.active is True

    def test_init_default_callback_data_int_type(self):
        """Input[int] without callback_data should fallback to component_id"""
        inp = Input[int](validation_function=int)
        assert inp.callback_data == inp.component_id

    def test_init_explicit_callback_data_int_type(self):
        """Input[int] with explicit callback_data should use it"""
        inp = Input[int](validation_function=int, callback_data="x")
        assert inp.callback_data == "x"

    def test_duplicate_callback_data_in_screen_raises(self):
        """Two Inputs with same explicit callback_data in a Screen should raise ValueError"""
        from tuican.components import Screen

        class DupScreen(Screen):
            def __init__(self):
                self.inp1 = Input[int](validation_function=int, callback_data="dup")
                self.inp2 = Input[int](validation_function=int, callback_data="dup")
                super().__init__([self.inp1, self.inp2], message="test")

            def get_layout(self):
                return [[self.inp1], [self.inp2]]

        with pytest.raises(ValueError, match="Duplicate callback_data"):
            DupScreen()
