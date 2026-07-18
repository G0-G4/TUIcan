import pytest
from unittest.mock import MagicMock, AsyncMock

from tuican.components import Screen, Input


class TwoInputScreen(Screen):
    def __init__(self):
        self.input_a = Input[str](validation_function=lambda x: x, text="A:", callback_data="a")
        self.input_b = Input[int](validation_function=int, text="B:", callback_data="b")
        super().__init__([self.input_a, self.input_b], message="test")

    def get_layout(self):
        return [
            [self.input_a],
            [self.input_b],
        ]


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.callback_query = None
    update.message = None
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.bot = MagicMock()
    return context


class TestScreenFocus:
    @pytest.mark.asyncio
    async def test_set_focus_deactivates_other_inputs(self, mock_update, mock_context):
        """set_focus should deactivate all other active MessageHandlingComponents"""
        screen = TwoInputScreen()

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.set_focus(screen.input_a)

        assert screen.input_a.active is False  # input_a was not active, stays inactive
        assert screen.input_b.active is False    # input_b was active but not focused, so it was deactivated

    @pytest.mark.asyncio
    async def test_activate_input_deactivates_other_active_input(self, mock_update, mock_context):
        """Activating one input should automatically deactivate another active input via set_focus"""
        screen = TwoInputScreen()

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.input_a.activate()

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_toggle_input_deactivates_other_active_input(self, mock_update, mock_context):
        """Toggling one input on should deactivate another active input via set_focus"""
        screen = TwoInputScreen()

        await screen.input_b.activate()
        assert screen.input_b.active is True

        await screen.input_a.toggle()

        assert screen.input_a.active is True
        assert screen.input_b.active is False

    @pytest.mark.asyncio
    async def test_parent_screen_set_on_registration(self, mock_update, mock_context):
        """Components should have parent_screen set when registered to a Screen"""
        screen = TwoInputScreen()

        assert screen.input_a.parent_screen is screen
        assert screen.input_b.parent_screen is screen

    @pytest.mark.asyncio
    async def test_set_focus_ignores_inactive_components(self, mock_update, mock_context):
        """set_focus should not call deactivate on components that are already inactive"""
        screen = TwoInputScreen()

        screen.input_a.deactivate = AsyncMock()
        screen.input_b.deactivate = AsyncMock()

        await screen.set_focus(screen.input_a)

        screen.input_a.deactivate.assert_not_awaited()
        screen.input_b.deactivate.assert_not_awaited()


class TestScreenLifecycleMethods:
    @pytest.mark.asyncio
    async def test_on_start_exists_and_is_callable(self, mock_update, mock_context):
        screen = TwoInputScreen()
        assert hasattr(screen, "on_start")
        assert callable(screen.on_start)
        await screen.on_start(mock_update, mock_context)

    def test_start_handler_is_alias_for_on_start(self):
        assert Screen.start_handler is Screen.on_start

    @pytest.mark.asyncio
    async def test_on_command_exists_and_is_callable(self, mock_update, mock_context):
        screen = TwoInputScreen()
        assert hasattr(screen, "on_command")
        assert callable(screen.on_command)
        await screen.on_command([], mock_update, mock_context)

    def test_command_handler_is_alias_for_on_command(self):
        assert Screen.command_handler is Screen.on_command


class TestScreenDeleteComponents:
    def test_delete_components_reduces_components_list(self):
        from tuican.components.button import Button
        from tuican.components.checkbox import CheckBox
        from tuican.components.input import Input

        class ThreeCompScreen(Screen):
            def __init__(self):
                self.btn = Button(text="btn", callback_data="btn_cb")
                self.chk = CheckBox(text="chk", callback_data="chk_cb")
                self.inp = Input[str](validation_function=lambda x: x, text="inp", callback_data="inp_cb")
                super().__init__([self.btn, self.chk, self.inp], message="test")

            def get_layout(self):
                return [[self.btn], [self.chk], [self.inp]]

        screen = ThreeCompScreen()
        screen.delete_components([screen.btn, screen.inp])
        assert len(screen._components) == 1
        assert screen._components[0] is screen.chk
        assert "btn_cb" not in screen._callback_map
        assert "inp_cb" not in screen._callback_map
        assert "chk_cb" in screen._callback_map
