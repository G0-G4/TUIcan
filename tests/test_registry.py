import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import Update, CallbackQuery, Message

from tuican.components.registry import ComponentRegistry
from tuican.components.component import Component, MessageHandlingComponent
from tuican.keyboard_button import KeyboardButton


class MockComponent(Component):
    def __init__(self, callback_data="cb", component_id=None):
        super().__init__(callback_data=callback_data, component_id=component_id)

    async def handle_callback(self):
        return True

    def render(self):
        return KeyboardButton(text="mock", callback_data=self.callback_data)


class MockMessageComponent(MessageHandlingComponent):
    def __init__(self, callback_data="msg_cb", component_id=None):
        super().__init__(callback_data=callback_data, component_id=component_id)
        self.deactivate = AsyncMock()
        self.handle_message = AsyncMock(return_value=True)

    async def handle_callback(self):
        return True

    def render(self):
        return KeyboardButton(text="msg", callback_data=self.callback_data)

    async def deactivate(self):
        pass

    async def handle_message(self):
        return True


class TestComponentRegistry:
    @pytest.fixture
    def mock_screen(self):
        screen = MagicMock()
        screen.update = None
        screen.context = None
        return screen

    def test_init_registers_components(self, mock_screen):
        c1 = MockComponent(callback_data="a")
        c2 = MockComponent(callback_data="b")
        registry = ComponentRegistry([c1, c2], parent_screen=mock_screen)
        assert registry.components == [c1, c2]
        assert registry.callback_map == {"a": c1, "b": c2}
        assert c1.parent_screen is mock_screen
        assert c2.parent_screen is mock_screen

    def test_add_component(self, mock_screen):
        c1 = MockComponent(callback_data="a")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        c2 = MockComponent(callback_data="b")
        registry.add_component(c2)
        assert c2 in registry.components
        assert registry.callback_map["b"] is c2
        assert c2.parent_screen is mock_screen

    def test_add_components(self, mock_screen):
        c1 = MockComponent(callback_data="a")
        registry = ComponentRegistry([], parent_screen=mock_screen)
        c2 = MockComponent(callback_data="b")
        c3 = MockComponent(callback_data="c")
        registry.add_components([c2, c3])
        assert registry.components == [c2, c3]
        assert registry.callback_map == {"b": c2, "c": c3}

    def test_delete_component(self, mock_screen):
        c1 = MockComponent(callback_data="a")
        c2 = MockComponent(callback_data="b")
        registry = ComponentRegistry([c1, c2], parent_screen=mock_screen)
        registry.delete_component(c1)
        assert c1 not in registry.components
        assert "a" not in registry.callback_map
        assert "b" in registry.callback_map

    def test_delete_component_clears_active_message_component(self, mock_screen):
        msg_comp = MockMessageComponent(callback_data="msg")
        registry = ComponentRegistry([msg_comp], parent_screen=mock_screen)
        registry._active_message_component = msg_comp
        registry.delete_component(msg_comp)
        assert registry.active_message_component is None
        assert msg_comp not in registry._message_components

    @pytest.mark.asyncio
    async def test_dispatcher_routes_callback(self, mock_screen):
        c1 = MockComponent(callback_data="cb1")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "cb1"
        result = await registry.dispatcher(update)
        assert result is True

    @pytest.mark.asyncio
    async def test_dispatcher_no_callback_query(self, mock_screen):
        c1 = MockComponent(callback_data="cb1")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        update = MagicMock(spec=Update)
        update.callback_query = None
        result = await registry.dispatcher(update)
        assert result is False

    @pytest.mark.asyncio
    async def test_dispatcher_unknown_callback_data(self, mock_screen):
        c1 = MockComponent(callback_data="cb1")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "unknown"
        result = await registry.dispatcher(update)
        assert result is False

    @pytest.mark.asyncio
    async def test_message_dispatcher_with_active_component(self, mock_screen):
        msg_comp = MockMessageComponent(callback_data="msg")
        registry = ComponentRegistry([msg_comp], parent_screen=mock_screen)
        registry._active_message_component = msg_comp
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        result = await registry.message_dispatcher(update)
        assert result is True

    @pytest.mark.asyncio
    async def test_message_dispatcher_no_active_component(self, mock_screen):
        msg_comp = MockMessageComponent(callback_data="msg")
        registry = ComponentRegistry([msg_comp], parent_screen=mock_screen)
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        result = await registry.message_dispatcher(update)
        assert result is False

    @pytest.mark.asyncio
    async def test_message_dispatcher_no_message(self, mock_screen):
        msg_comp = MockMessageComponent(callback_data="msg")
        registry = ComponentRegistry([msg_comp], parent_screen=mock_screen)
        registry._active_message_component = msg_comp
        update = MagicMock(spec=Update)
        update.message = None
        result = await registry.message_dispatcher(update)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_focus_deactivates_previous(self, mock_screen):
        msg1 = MockMessageComponent(callback_data="msg1")
        msg2 = MockMessageComponent(callback_data="msg2")
        registry = ComponentRegistry([msg1, msg2], parent_screen=mock_screen)
        registry._active_message_component = msg1
        await registry.set_focus(msg2)
        msg1.deactivate.assert_awaited_once()
        assert registry.active_message_component is msg2

    @pytest.mark.asyncio
    async def test_set_focus_same_component_no_deactivate(self, mock_screen):
        msg1 = MockMessageComponent(callback_data="msg1")
        registry = ComponentRegistry([msg1], parent_screen=mock_screen)
        registry._active_message_component = msg1
        await registry.set_focus(msg1)
        msg1.deactivate.assert_not_awaited()
        assert registry.active_message_component is msg1

    @pytest.mark.asyncio
    async def test_set_focus_to_none_deactivates(self, mock_screen):
        msg1 = MockMessageComponent(callback_data="msg1")
        registry = ComponentRegistry([msg1], parent_screen=mock_screen)
        registry._active_message_component = msg1
        await registry.set_focus(None)
        msg1.deactivate.assert_awaited_once()
        assert registry.active_message_component is None

    def test_duplicate_callback_data_raises(self, mock_screen):
        c1 = MockComponent(callback_data="dup")
        c2 = MockComponent(callback_data="dup")
        with pytest.raises(ValueError, match="Duplicate callback_data"):
            ComponentRegistry([c1, c2], parent_screen=mock_screen)

    def test_same_component_duplicate_callback_data_ok(self, mock_screen):
        c1 = MockComponent(callback_data="dup")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        registry.add_component(c1)  # same instance, should not raise
        assert registry.callback_map["dup"] is c1

    def test_callback_map_consistency_after_add_and_delete(self, mock_screen):
        c1 = MockComponent(callback_data="a")
        c2 = MockComponent(callback_data="b")
        c3 = MockComponent(callback_data="c")
        registry = ComponentRegistry([c1], parent_screen=mock_screen)
        registry.add_component(c2)
        registry.add_component(c3)
        assert set(registry.callback_map.keys()) == {"a", "b", "c"}
        registry.delete_component(c2)
        assert set(registry.callback_map.keys()) == {"a", "c"}
        assert registry.callback_map["a"] is c1
        assert registry.callback_map["c"] is c3

    def test_clear_active_message_component(self, mock_screen):
        msg1 = MockMessageComponent(callback_data="msg1")
        registry = ComponentRegistry([msg1], parent_screen=mock_screen)
        registry._active_message_component = msg1
        registry.clear_active_message_component(msg1)
        assert registry.active_message_component is None

    def test_clear_active_message_component_different_component(self, mock_screen):
        msg1 = MockMessageComponent(callback_data="msg1")
        msg2 = MockMessageComponent(callback_data="msg2")
        registry = ComponentRegistry([msg1, msg2], parent_screen=mock_screen)
        registry._active_message_component = msg1
        registry.clear_active_message_component(msg2)
        assert registry.active_message_component is msg1

    def test_delete_components_removes_from_callback_map_and_message_components(self, mock_screen):
        from tuican.components.button import Button
        from tuican.components.checkbox import CheckBox
        from tuican.components.input import Input

        btn = Button(text="btn", callback_data="btn_cb")
        chk = CheckBox(text="chk", callback_data="chk_cb")
        inp = Input[str](validation_function=lambda x: x, text="inp", callback_data="inp_cb")
        registry = ComponentRegistry([btn, chk, inp], parent_screen=mock_screen)
        registry.delete_components([btn, inp])
        assert btn not in registry.components
        assert inp not in registry.components
        assert chk in registry.components
        assert "btn_cb" not in registry.callback_map
        assert "inp_cb" not in registry.callback_map
        assert "chk_cb" in registry.callback_map
        assert inp not in registry._message_components

    def test_delete_components_clears_active_message_component(self, mock_screen):
        from tuican.components.input import Input

        inp1 = Input[str](validation_function=lambda x: x, text="inp1", callback_data="inp1_cb")
        inp2 = Input[str](validation_function=lambda x: x, text="inp2", callback_data="inp2_cb")
        registry = ComponentRegistry([inp1, inp2], parent_screen=mock_screen)
        registry._active_message_component = inp1
        registry.delete_components([inp1])
        assert registry.active_message_component is None
        assert inp1 not in registry._message_components
        assert inp2 in registry._message_components
