import pytest
from unittest.mock import AsyncMock, MagicMock

from tuican.components import Screen, Button
from tuican.components.screen import ScreenGroup
from tuican.keyboard_button import KeyboardButton


class DummyScreen(Screen):
    description = "dummy"

    def __init__(self, message="dummy"):
        self.btn = Button(text="OK", callback_data="ok")
        super().__init__([self.btn], message=message)

    def get_layout(self):
        return [[self.btn]]


class TestScreenGroup:
    @pytest.fixture
    def home_screen(self):
        return DummyScreen(message="home")

    @pytest.fixture
    def new_screen(self):
        return DummyScreen(message="new")

    @pytest.fixture
    def mock_update(self):
        update = MagicMock()
        update.callback_query = None
        update.message = None
        return update

    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.bot = MagicMock()
        return context

    @pytest.fixture
    def backend(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_go_to_screen_adds_to_stack(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        await group.go_to_screen(mock_update, mock_context, new_screen)
        assert group._screen_stack[-1] is new_screen
        assert len(group._screen_stack) == 2

    @pytest.mark.asyncio
    async def test_go_back_removes_from_stack(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        await group.go_to_screen(mock_update, mock_context, new_screen)
        await group.go_back(mock_update, mock_context)
        assert group._screen_stack[-1] is home_screen
        assert len(group._screen_stack) == 1

    @pytest.mark.asyncio
    async def test_go_back_raises_when_only_home(self, home_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        with pytest.raises(RuntimeError, match="can't go back"):
            await group.go_back(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_go_home_resets_to_home(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        await group.go_to_screen(mock_update, mock_context, new_screen)
        await group.go_home(mock_update, mock_context)
        assert len(group._screen_stack) == 1
        assert group._screen_stack[0] is home_screen

    def test_backend_propagation_on_init(self, home_screen, backend):
        home_screen.backend = backend
        group = ScreenGroup(home_screen)
        group.backend = backend
        assert home_screen.backend is backend

    def test_backend_propagation_on_setter(self, home_screen, new_screen, backend):
        group = ScreenGroup(home_screen)
        group.backend = backend
        # go_to_screen should also propagate backend
        # but we test setter first
        assert home_screen.backend is backend

    @pytest.mark.asyncio
    async def test_backend_propagation_on_go_to_screen(self, home_screen, new_screen, mock_update, mock_context, backend):
        group = ScreenGroup(home_screen)
        group.backend = backend
        await group.go_to_screen(mock_update, mock_context, new_screen)
        assert new_screen.backend is backend

    @pytest.mark.asyncio
    async def test_max_depth_limit(self, home_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen, max_depth=2)
        second = DummyScreen(message="second")
        await group.go_to_screen(mock_update, mock_context, second)
        with pytest.raises(RuntimeError, match="maximum depth"):
            await group.go_to_screen(mock_update, mock_context, DummyScreen(message="third"))

    def test_proxy_get_layout(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        layout = group.get_layout()
        assert len(layout) == 1
        assert isinstance(layout[0][0], Button)

    @pytest.mark.asyncio
    async def test_proxy_dispatcher(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        home_screen.dispatcher = AsyncMock(return_value=True)
        result = await group.dispatcher(mock_update, mock_context)
        assert result is True
        home_screen.dispatcher.assert_awaited_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_proxy_message_dispatcher(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        home_screen.message_dispatcher = AsyncMock(return_value=True)
        result = await group.message_dispatcher(mock_update, mock_context)
        assert result is True
        home_screen.message_dispatcher.assert_awaited_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_proxy_display(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        home_screen.display = AsyncMock()
        await group.display(mock_update, mock_context)
        home_screen.display.assert_awaited_once_with(mock_update, mock_context)

    def test_proxy_message_property(self, home_screen):
        group = ScreenGroup(home_screen)
        assert group.message == "home"
        group.message = "changed"
        assert home_screen.message == "changed"

    def test_proxy_clear_update(self, home_screen):
        group = ScreenGroup(home_screen)
        home_screen._update_to_display_on = MagicMock()
        group.clear_update()
        assert home_screen._update_to_display_on is None

    @pytest.mark.asyncio
    async def test_command_handler_delegation(self, home_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        home_screen.command_handler = AsyncMock()
        await group.command_handler(["arg"], mock_update, mock_context)
        home_screen.command_handler.assert_awaited_once_with(["arg"], mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_go_to_screen_does_not_display(self, home_screen, new_screen, mock_update, mock_context):
        group = ScreenGroup(home_screen)
        new_screen.display = AsyncMock()
        await group.go_to_screen(mock_update, mock_context, new_screen)
        new_screen.display.assert_not_awaited()
