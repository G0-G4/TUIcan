import pytest
from unittest.mock import MagicMock
from tuican.keyboard_button import KeyboardButton
from tuican.components.checkbox import CheckBox, ExclusiveCheckBoxGroup


class TestCheckBox:
    def test_init_default_values(self):
        """CheckBox should initialize with default values"""
        cb = CheckBox(text="Option")
        assert cb.text == "Option"
        assert cb.selected is False
        assert cb.callback_data == cb.component_id

    def test_init_with_group(self):
        """CheckBox should register itself with a group"""
        group = ExclusiveCheckBoxGroup()
        cb = CheckBox(text="Option", group=group)
        assert cb in group._checkboxes

    def test_text_setter(self):
        """CheckBox text should be changeable"""
        cb = CheckBox(text="Old")
        cb.text = "New"
        assert cb.text == "New"

    def test_render_unchecked(self, mock_screen):
        """render() should show unchecked state"""
        cb = CheckBox(text="Option", selected=False)
        cb.parent_screen = mock_screen
        result = cb.render()

        assert isinstance(result, KeyboardButton)
        assert result.text == "Option"
        assert result.callback_data == cb.callback_data

    def test_render_checked(self, mock_screen):
        """render() should show checked state with checkmark"""
        cb = CheckBox(text="Option", selected=True)
        cb.parent_screen = mock_screen
        result = cb.render()

        assert isinstance(result, KeyboardButton)
        assert result.text == "✓ Option"

    @pytest.mark.asyncio
    async def test_handle_callback_mismatch_returns_false(self, mock_screen):
        """handle_callback should return False when callback_data doesn't match"""
        cb = CheckBox(text="Test", callback_data="correct")
        cb.parent_screen = mock_screen
        mock_screen.update.callback_query.data = "wrong"
        result = await cb.handle_callback()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_callback_match_toggles(self, mock_screen):
        """handle_callback should toggle the checkbox when callback_data matches"""
        cb = CheckBox(text="Test", callback_data="match")
        cb.parent_screen = mock_screen

        assert cb.selected is False

        mock_screen.update.callback_query.data = "match"
        result = await cb.handle_callback()

        assert result is True
        assert cb.selected is True

    @pytest.mark.asyncio
    async def test_check_changes_state(self, mock_screen):
        """check() should set selected to True"""
        cb = CheckBox(text="Test")
        cb.parent_screen = mock_screen
        assert cb.selected is False

        await cb.check()
        assert cb.selected is True

    @pytest.mark.asyncio
    async def test_uncheck_changes_state(self, mock_screen):
        """uncheck() should set selected to False"""
        cb = CheckBox(text="Test", selected=True)
        cb.parent_screen = mock_screen
        assert cb.selected is True

        await cb.uncheck()
        assert cb.selected is False

    @pytest.mark.asyncio
    async def test_toggle_changes_state(self, mock_screen):
        """toggle() should flip selected state"""
        cb = CheckBox(text="Test")
        cb.parent_screen = mock_screen
        assert cb.selected is False

        await cb.toggle()
        assert cb.selected is True

        await cb.toggle()
        assert cb.selected is False

    @pytest.mark.asyncio
    async def test_check_triggers_on_change_without_group(self, mock_screen):
        """check() should trigger on_change handler even without a group"""
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        cb = CheckBox(text="Test", on_change=handler)
        cb.parent_screen = mock_screen
        await cb.check()

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_check_triggers_on_change_with_group(self, mock_screen):
        """check() should trigger on_change handler when part of a group"""
        handler_called = False

        async def handler():
            nonlocal handler_called
            handler_called = True

        group = ExclusiveCheckBoxGroup()
        cb = CheckBox(text="Test", on_change=handler, group=group)
        cb.parent_screen = mock_screen
        await cb.check()

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_no_duplicate_on_change_when_already_checked(self, mock_screen):
        """check() should not trigger on_change if already selected"""
        handler_calls = 0

        async def handler():
            nonlocal handler_calls
            handler_calls += 1

        cb = CheckBox(text="Test", selected=True, on_change=handler)
        cb.parent_screen = mock_screen
        await cb.check()

        assert handler_calls == 0


class TestExclusiveCheckBoxGroup:
    def test_add_checkbox(self):
        """add() should add checkbox to group"""
        group = ExclusiveCheckBoxGroup()
        cb = CheckBox(text="Test")
        group.add(cb)
        assert cb in group._checkboxes

    def test_add_all(self):
        """add_all() should add multiple checkboxes"""
        group = ExclusiveCheckBoxGroup()
        cb1 = CheckBox(text="1")
        cb2 = CheckBox(text="2")
        group.add_all([cb1, cb2])
        assert len(group._checkboxes) == 2

    async def test_notify_unchecks_others(self):
        """notify() should uncheck other checkboxes"""
        group = ExclusiveCheckBoxGroup()
        cb1 = CheckBox(text="1", selected=True, group=group)
        cb2 = CheckBox(text="2", selected=False, group=group)

        await group.notify(cb2)

        assert cb1.selected is False

    async def test_notify_sticky(self):
        """sticky group should prevent unchecking the notifier"""
        group = ExclusiveCheckBoxGroup(sticky=True)
        cb = CheckBox(text="Test", selected=True, group=group)

        await group.notify(cb)

        assert cb.selected is True

    def test_get_selected(self):
        """get_selected() should return the selected checkbox"""
        group = ExclusiveCheckBoxGroup()
        cb1 = CheckBox(text="1", selected=False, group=group)
        cb2 = CheckBox(text="2", selected=True, group=group)

        result = group.get_selected()
        assert result == cb2

    def test_get_selected_none(self):
        """get_selected() should return None when nothing is selected"""
        group = ExclusiveCheckBoxGroup()
        cb = CheckBox(text="Test", selected=False, group=group)

        result = group.get_selected()
        assert result is None
