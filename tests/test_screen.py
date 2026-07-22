import pytest
from unittest.mock import AsyncMock, MagicMock

from tuican.backend import MessageBackend
from tuican.components import Screen, Input
from tuican.update import TuicanUpdate, UpdateKind


class TwoInputScreen(Screen):
    def __init__(self, backend: MessageBackend):
        self.input_a = Input[str](validation_function=lambda x: x, text="A:", callback_data="a")
        self.input_b = Input[int](validation_function=int, text="B:", callback_data="b")
        super().__init__([self.input_a, self.input_b], message="test", backend=backend)

    def get_layout(self):
        return [
            [self.input_a],
            [self.input_b],
        ]


@pytest.fixture
def mock_update():
    return TuicanUpdate.from_message(
        user_id=1,
        chat_id=1,
        message_text="test",
        message_id=1,
    )


@pytest.fixture
def backend():
    return MagicMock(spec=MessageBackend)


class TestScreenFocus:
    @pytest.mark.asyncio
    async def test_set_focus_deactivates_other_inputs(self, backend):
        """set_focus should deactivate others and activate the focused input"""
        screen = TwoInputScreen(backend=backend)

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.set_focus(screen.input_a)

        assert screen.input_a.active is True  # focused input must accept messages
        assert screen.input_b.active is False  # previous focus was deactivated

    @pytest.mark.asyncio
    async def test_activate_input_deactivates_other_active_input(self, backend):
        """Activating one input should automatically deactivate another active input via set_focus"""
        screen = TwoInputScreen(backend=backend)

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.input_a.activate()

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_toggle_input_deactivates_other_active_input(self, backend):
        """Toggling one input on should deactivate another active input via set_focus"""
        screen = TwoInputScreen(backend=backend)

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.input_a.toggle()

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_parent_screen_set_on_registration(self, backend):
        """Components should have parent_screen set when registered to a Screen"""
        screen = TwoInputScreen(backend=backend)

        assert screen.input_a.parent_screen is screen
        assert screen.input_b.parent_screen is screen

    @pytest.mark.asyncio
    async def test_set_focus_deactivates_peers_even_if_inactive_flag(self, backend):
        """set_focus deactivates all other message components for exclusive UI state"""
        screen = TwoInputScreen(backend=backend)

        # Force a desynced peer that looks active while not in the registry
        screen.input_b._active = True
        screen.input_b.deactivate = AsyncMock(wraps=screen.input_b.deactivate)

        await screen.set_focus(screen.input_a)

        screen.input_b.deactivate.assert_awaited()
        assert screen.input_a.active is True

    @pytest.mark.asyncio
    async def test_set_focus_enables_message_handling(self, backend):
        """After set_focus, typed text must be accepted by the focused input"""
        from tuican.update import TuicanUpdate

        screen = TwoInputScreen(backend=backend)
        await screen.set_focus(screen.input_a)
        assert screen.input_a.active is True

        update = TuicanUpdate.from_message(
            user_id=1, chat_id=1, message_text="hello", message_id=1
        )
        screen._current_update = update
        handled = await screen.message_dispatcher(update)

        assert handled is True
        assert screen.input_a.value == "hello"
        assert screen.input_a.active is False

    @pytest.mark.asyncio
    async def test_set_focus_preserves_value(self, backend):
        """set_focus must not clear the input value (unlike activate default)"""
        screen = TwoInputScreen(backend=backend)
        screen.input_a.value = "existing"

        await screen.set_focus(screen.input_a)

        assert screen.input_a.active is True
        assert screen.input_a.value == "existing"

    @pytest.mark.asyncio
    async def test_toggle_switches_exclusive_active_prompt(self, backend):
        """Tapping another input moves active prompt and message routing exclusively"""
        from tuican.update import TuicanUpdate

        screen = TwoInputScreen(backend=backend)
        await screen.set_focus(screen.input_a)
        assert screen.input_a.active is True
        assert screen.input_b.active is False

        # User taps input_b
        screen._current_update = TuicanUpdate.from_callback(
            user_id=1, chat_id=1, callback_data=screen.input_b.callback_data, message_id=1
        )
        await screen.input_b.handle_callback()

        assert screen.input_a.active is False
        assert screen.input_b.active is True
        assert "Enter:" in screen.input_b.render().text
        assert "Enter:" not in screen.input_a.render().text

        # Typed text goes to input_b only
        screen._current_update = TuicanUpdate.from_message(
            user_id=1, chat_id=1, message_text="42", message_id=2
        )
        handled = await screen.message_dispatcher(screen._current_update)
        assert handled is True
        assert screen.input_b.value == 42
        assert screen.input_a.value is None

    @pytest.mark.asyncio
    async def test_toggle_same_input_twice_clears_focus(self, backend):
        """Second tap on the same input deactivates it"""
        from tuican.update import TuicanUpdate

        screen = TwoInputScreen(backend=backend)
        screen._current_update = TuicanUpdate.from_callback(
            user_id=1, chat_id=1, callback_data=screen.input_a.callback_data, message_id=1
        )
        await screen.input_a.handle_callback()
        assert screen.input_a.active is True

        await screen.input_a.handle_callback()
        assert screen.input_a.active is False
        assert screen._active_message_component is None


class TestScreenLifecycleMethods:
    @pytest.mark.asyncio
    async def test_on_start_exists_and_is_callable(self, mock_update, backend):
        screen = TwoInputScreen(backend=backend)
        assert hasattr(screen, "on_start")
        assert callable(screen.on_start)
        await screen.on_start(mock_update)

    @pytest.mark.asyncio
    async def test_on_command_exists_and_is_callable(self, mock_update, backend):
        screen = TwoInputScreen(backend=backend)
        assert hasattr(screen, "on_command")
        assert callable(screen.on_command)
        await screen.on_command([], mock_update)


class TestScreenDeleteComponents:
    def test_delete_components_reduces_components_list(self, backend):
        from tuican.components.button import Button
        from tuican.components.checkbox import CheckBox
        from tuican.components.input import Input

        class ThreeCompScreen(Screen):
            def __init__(self, backend: MessageBackend):
                self.btn = Button(text="btn", callback_data="btn_cb")
                self.chk = CheckBox(text="chk", callback_data="chk_cb")
                self.inp = Input[str](validation_function=lambda x: x, text="inp", callback_data="inp_cb")
                super().__init__([self.btn, self.chk, self.inp], message="test", backend=backend)

            def get_layout(self):
                return [[self.btn], [self.chk], [self.inp]]

        screen = ThreeCompScreen(backend=backend)
        screen.delete_components([screen.btn, screen.inp])
        assert len(screen._components) == 1
        assert screen._components[0] is screen.chk
        assert "btn_cb" not in screen._callback_map
        assert "inp_cb" not in screen._callback_map
        assert "chk_cb" in screen._callback_map
