import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes

CallBack = Callable[[Update, ContextTypes.DEFAULT_TYPE, str, "Component"], None] | Callable[
    [Update, ContextTypes.DEFAULT_TYPE, str, "Component"], Coroutine[Any, Any, None]]


class Component(ABC):
    def __init__(
            self,
            component_id: str = None,
            callback_data: str = None,
            on_change: CallBack | None = None):
        self._component_id = component_id or str(id(self))
        self._callback_data = callback_data or self.component_id
        self.on_change = on_change

    async def call_on_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if not self.on_change:
            return
        if asyncio.iscoroutinefunction(self.on_change):
            await self.on_change(update, context, callback_data, self)
        else:
            self.on_change(update, context, callback_data, self)

    @abstractmethod
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def render(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardButton:
        raise NotImplementedError


    @property
    def callback_data(self) -> str:
        return self._callback_data

    @property
    def component_id(self) -> str:
        return self._component_id


class MessageHandlingComponent(Component, ABC):
    @abstractmethod
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        raise NotImplementedError
