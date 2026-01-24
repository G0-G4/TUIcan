import asyncio
from abc import ABC, abstractmethod
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

CallBack = Callable[[Update, ContextTypes.DEFAULT_TYPE, str], None]


class Component(ABC):
    def __init__(self, component_id: str = None,
                 on_change: CallBack | None = None):
        self.component_id = component_id or str(id(self))
        self.on_change = on_change

    async def call_on_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        if not self.on_change:
            return
        if asyncio.iscoroutinefunction(self.on_change):
            await self.on_change(update, context, callback_data)
        else:
            self.on_change(update, context, callback_data)

    @abstractmethod
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              callback_data: str | None) -> bool:
        raise NotImplementedError


class MessageHandlingComponent(Component, ABC):
    @abstractmethod
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        raise NotImplementedError
