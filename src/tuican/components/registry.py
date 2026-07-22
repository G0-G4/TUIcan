from typing import TYPE_CHECKING

from ..update import TuicanUpdate
from .component import Component, MessageHandlingComponent

if TYPE_CHECKING:
    from .screen import Screen


class ComponentRegistry:
    """Encapsulates component registration, callback dispatching, and focus management."""

    def __init__(self, components: list[Component], parent_screen: "Screen | None" = None):
        self._parent_screen = parent_screen
        self._components: list[Component] = list(components)
        self._callback_map: dict[str, Component] = {}
        self._message_components: list[MessageHandlingComponent] = []
        self._active_message_component: MessageHandlingComponent | None = None
        for comp in components:
            self._register_component(comp)

    @property
    def components(self) -> list[Component]:
        return list(self._components)

    @property
    def callback_map(self) -> dict[str, Component]:
        return dict(self._callback_map)

    @property
    def active_message_component(self) -> MessageHandlingComponent | None:
        return self._active_message_component

    def add_component(self, comp: Component) -> None:
        self._components.append(comp)
        self._register_component(comp)

    def add_components(self, comps: list[Component]) -> None:
        for comp in comps:
            self.add_component(comp)

    def delete_component(self, comp: Component) -> None:
        self._components.remove(comp)
        self._unregister_component(comp)

    def delete_components(self, comps: list[Component]) -> None:
        for comp in comps:
            self.delete_component(comp)

    def _register_component(self, comp: Component) -> None:
        if comp.callback_data in self._callback_map:
            existing = self._callback_map[comp.callback_data]
            if existing is not comp:
                raise ValueError(
                    f"Duplicate callback_data {comp.callback_data!r} already registered by {existing!r}"
                )
        self._callback_map[comp.callback_data] = comp
        comp.parent_screen = self._parent_screen
        if isinstance(comp, MessageHandlingComponent):
            self._message_components.append(comp)

    def clear_active_message_component(self, component: MessageHandlingComponent) -> None:
        if self._active_message_component is component:
            self._active_message_component = None

    def _unregister_component(self, comp: Component) -> None:
        mapped = self._callback_map.get(comp.callback_data)
        if mapped is comp:
            del self._callback_map[comp.callback_data]
        if isinstance(comp, MessageHandlingComponent):
            if self._active_message_component is comp:
                self._active_message_component = None
            self._message_components.remove(comp)

    async def dispatcher(self, update: TuicanUpdate) -> bool:
        callback_data = update.callback_data
        if callback_data is not None:
            component = self._callback_map.get(callback_data)
            if component is not None:
                return await component.handle_callback()
        return False

    async def message_dispatcher(self, update: TuicanUpdate) -> bool:
        message_text = update.message_text
        if message_text is not None and self._active_message_component is not None:
            return await self._active_message_component.handle_message()
        return False

    async def set_focus(self, focused_component: MessageHandlingComponent | None) -> None:
        """Set which component receives text messages.

        Deactivates the previous focused component (if any), then marks the new
        one as accepting messages via ``accept_focus()`` without clearing its
        value or firing ``on_change``.
        """
        if self._active_message_component is not None and self._active_message_component is not focused_component:
            await self._active_message_component.deactivate()
        self._active_message_component = focused_component
        if focused_component is not None:
            focused_component.accept_focus()
