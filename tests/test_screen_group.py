import pytest
from unittest.mock import AsyncMock, MagicMock

from tuican.backend import MessageBackend
from tuican.components import Screen, Button
from tuican.components.screen import ScreenGroup
from tuican.keyboard_button import KeyboardButton
from tuican.update import TuicanUpdate, UpdateKind


class DummyScreen(Screen):
    description = "dummy"

    def __init__(self, message="dummy", backend: MessageBackend | None = None):
        self.btn = Button(text="OK", callback_data="ok")
        super().__init__([self.btn], message=message, backend=backend)

    def get_layout(self):
        return [[self.btn]]


class TestScreenGroup:
    @pytest.fixture
    def home_screen(self, backend):
        return DummyScreen(message="home", backend=backend)

    @pytest.fixture
    def new_screen(self, backend):
        return DummyScreen(message="new", backend=backend)

    @pytest.fixture
    def mock_update(self):
        return TuicanUpdate.from_message(
            user_id=1,
            chat_id=1,
            message_text="test",
            message_id=1,
        )

    @pytest.fixture
    def backend(self):
        return MagicMock(spec=MessageBackend)

    @pytest.mark.asyncio
    async def test_go_to_screen_adds_to_stack(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        await group.go_to_screen(mock_update, new_screen)
        assert group._screen_stack[-1] is new_screen
        assert len(group._screen_stack) == 2

    @pytest.mark.asyncio
    async def test_go_back_removes_from_stack(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        await group.go_to_screen(mock_update, new_screen)
        await group.go_back(mock_update)
        assert group._screen_stack[-1] is home_screen
        assert len(group._screen_stack) == 1

    @pytest.mark.asyncio
    async def test_go_back_raises_when_only_home(self, home_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        with pytest.raises(RuntimeError, match="can't go back"):
            await group.go_back(mock_update)

    @pytest.mark.asyncio
    async def test_go_home_resets_to_home(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        await group.go_to_screen(mock_update, new_screen)
        await group.go_home(mock_update)
        assert len(group._screen_stack) == 1
        assert group._screen_stack[0] is home_screen

    def test_backend_propagation_on_init(self, home_screen, backend):
        group = ScreenGroup(home_screen, backend=backend)
        assert home_screen.backend is backend

    def test_backend_propagation_on_setter(self, home_screen, new_screen, backend):
        group = ScreenGroup(home_screen, backend=backend)
        # go_to_screen should also propagate backend
        # but we test setter first
        assert home_screen.backend is backend

    @pytest.mark.asyncio
    async def test_backend_propagation_on_go_to_screen(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        await group.go_to_screen(mock_update, new_screen)
        assert new_screen.backend is backend

    @pytest.mark.asyncio
    async def test_max_depth_limit(self, home_screen, mock_update, backend):
        group = ScreenGroup(home_screen, max_depth=2, backend=backend)
        second = DummyScreen(message="second", backend=backend)
        await group.go_to_screen(mock_update, second)
        with pytest.raises(RuntimeError, match="maximum depth"):
            await group.go_to_screen(mock_update, DummyScreen(message="third", backend=backend))

    def test_proxy_get_layout(self, home_screen, backend):
        group = ScreenGroup(home_screen, backend=backend)
        layout = group.get_layout()
        assert len(layout) == 1
        assert isinstance(layout[0][0], Button)

    @pytest.mark.asyncio
    async def test_proxy_dispatcher(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen.dispatcher = AsyncMock(return_value=True)
        result = await group.dispatcher(mock_update)
        assert result is True
        home_screen.dispatcher.assert_awaited_once_with(mock_update)

    @pytest.mark.asyncio
    async def test_proxy_message_dispatcher(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen.message_dispatcher = AsyncMock(return_value=True)
        result = await group.message_dispatcher(mock_update)
        assert result is True
        home_screen.message_dispatcher.assert_awaited_once_with(mock_update)

    @pytest.mark.asyncio
    async def test_proxy_display(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen.display = AsyncMock()
        await group.display(mock_update)
        home_screen.display.assert_awaited_once_with(mock_update)

    def test_proxy_message_property(self, home_screen, backend):
        group = ScreenGroup(home_screen, backend=backend)
        assert group.message == "home"
        group.message = "changed"
        assert home_screen.message == "changed"

    def test_proxy_clear_update(self, home_screen, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen._update_to_display_on = MagicMock()
        group.clear_update()
        assert home_screen._update_to_display_on is None

    @pytest.mark.asyncio
    async def test_proxy_clear_update_delegates_to_top_screen(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        await group.go_to_screen(mock_update, new_screen)
        new_screen._update_to_display_on = MagicMock()
        new_screen.clear_update = MagicMock()
        group.clear_update()
        new_screen.clear_update.assert_called_once()
        # If the group had directly mutated the field, this would be None
        assert new_screen._update_to_display_on is not None

    @pytest.mark.asyncio
    async def test_on_command_delegation(self, home_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen.on_command = AsyncMock()
        await group.on_command(["arg"], mock_update)
        home_screen.on_command.assert_awaited_once_with(["arg"], mock_update)

    @pytest.mark.asyncio
    async def test_command_handler_alias_delegation(self, home_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        home_screen.on_command = AsyncMock()
        await group.command_handler(["arg"], mock_update)
        home_screen.on_command.assert_awaited_once_with(["arg"], mock_update)

    @pytest.mark.asyncio
    async def test_go_to_screen_does_not_display(self, home_screen, new_screen, mock_update, backend):
        group = ScreenGroup(home_screen, backend=backend)
        new_screen.display = AsyncMock()
        await group.go_to_screen(mock_update, new_screen)
        new_screen.display.assert_not_awaited()
