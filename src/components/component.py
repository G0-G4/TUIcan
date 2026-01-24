import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes


class Component(ABC):
    def __init__(self, component_id: str = None,
                 on_change: Callable[[Any, Update, ContextTypes.DEFAULT_TYPE], None] | None = None):
        self.component_id = component_id or str(id(self))
        self.on_change = on_change

    async def call_on_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.on_change:
            return
        if asyncio.iscoroutinefunction(self.on_change):
            await self.on_change(self, update, context)
        else:
            self.on_change(self, update, context)

    @abstractmethod
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> bool:
        raise NotImplementedError
