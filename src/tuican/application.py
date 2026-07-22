from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from .backend import MessageBackend
from .components import Screen
from .components.screen import StartScreenProtocol
from .errors import UserNotFoundError, ValidationError
from .state_store import StateStore
from .stores import InMemoryStateStore
from .update import TuicanUpdate, get_user_id

if TYPE_CHECKING:
    from .transports.base import Transport

Middleware = Callable[[TuicanUpdate], Coroutine[Any, Any, bool]]


class Application:
    def __init__(
        self,
        token: str,
        screens: dict[str, StartScreenProtocol],
        *,
        transport: "Transport | str" = "ptb",
        state_store: StateStore | None = None,
        backend: MessageBackend | None = None,
        api_id: int | None = None,
        api_hash: str | None = None,
    ):
        self._token = token
        self._screen_factories = screens
        self._user_screens: dict[tuple[str, int], Screen] = {}
        self._max_user_screens = 10_000
        self._user_commands: dict[int, str] = {}
        self._max_user_commands = 10_000
        self._state_store = state_store or InMemoryStateStore()
        self._middlewares: list[Middleware] = []
        self._transport: Transport

        if isinstance(transport, str):
            if transport == "ptb":
                from tuican.transports.ptb_transport import PtbTransport
                self._transport = PtbTransport(token)
            elif transport == "telethon":
                from tuican.transports.telethon_transport import TelethonTransport
                self._transport = TelethonTransport(token, api_id, api_hash)
            else:
                raise ValueError(f"Unknown transport: {transport}")
        else:
            self._transport = transport

        self._backend = backend

    @property
    def backend(self) -> MessageBackend:
        if self._backend is None:
            self._backend = self._transport.default_backend()
        assert self._backend is not None
        return self._backend

    @property
    def screens(self) -> dict[str, StartScreenProtocol]:
        return self._screen_factories

    @property
    def state_store(self) -> StateStore:
        return self._state_store

    def middleware(self, function: Middleware):
        self._middlewares.append(function)
        return function

    async def _run_middlewares(self, update: TuicanUpdate) -> bool:
        for mw in self._middlewares:
            result = await mw(update)
            if result is False:
                return False
        return True

    def run(self):
        self._transport.start(self)
        self._transport.run()

    def run_webhook(self, webhook_url: str, listen: str = "0.0.0.0", port: int = 8080, **kwargs):
        self._transport.start(self)
        self._transport.run_webhook(
            webhook_url=webhook_url,
            listen=listen,
            port=port,
            **kwargs,
        )

    async def handle_exception(self, e: Exception, update: TuicanUpdate):
        logging.getLogger(__name__).exception("Unhandled exception in update handler")
        await self.backend.send_plain_message(
            update, "An unexpected error occurred. Please try again later."
        )

    async def command_handler(self, update: TuicanUpdate):
        if not await self._run_middlewares(update):
            return
        try:
            await self.remove_current_screen(update)
            message_text = update.message_text
            if message_text is None or not message_text.startswith("/"):
                return
            command_args = message_text.replace("/", "").split()
            await self._set_user_command(update, command_args[0])
            screen = await self.get_or_create_screen(update, command_args)
            screen.clear_update()
            await screen.on_start(update)
        except (UserNotFoundError, KeyError) as e:
            logging.getLogger(__name__).warning("Bad update in command_handler: %s", e)

    async def dispatcher(self, update: TuicanUpdate):
        if not await self._run_middlewares(update):
            return
        screen = await self.get_or_create_screen(update)
        try:
            if await screen.dispatcher(update):
                await screen.display(update)
        except Exception as e:
            await self.handle_exception(e, update)

    async def message_dispatcher(self, update: TuicanUpdate):
        if not await self._run_middlewares(update):
            return
        screen = await self.get_or_create_screen(update)
        try:
            if await screen.message_dispatcher(update):
                message_id_to_delete = update.message_id
                if message_id_to_delete is None:
                    return
                await screen.display(update)
                await self.backend.delete_message(
                    update, message_id_to_delete
                )
        except ValidationError as e:
            await self.backend.send_plain_message(update, str(e))
        except Exception as e:
            await self.handle_exception(e, update)

    def _enforce_limits(self) -> None:
        while len(self._user_screens) > self._max_user_screens:
            self._user_screens.pop(next(iter(self._user_screens)))
        while len(self._user_commands) > self._max_user_commands:
            self._user_commands.pop(next(iter(self._user_commands)))

    async def get_or_create_screen(self, update: TuicanUpdate, args=None):
        command = self._get_user_command(update)
        not_initiated = command is None
        if not_initiated:
            logging.getLogger(__name__).info("command is empty. possible press on button after restart. start will be shown")
            command = "start"
            await self._set_user_command(update, command)
        assert command is not None
        user_id = get_user_id(update)
        if command not in self._screen_factories:
            raise KeyError(f"Unknown command: {command}")
        factory = self._screen_factories[command]
        key: tuple[str, int] = (command, user_id)
        screen = self._user_screens.get(key)
        if screen is None:
            screen = factory()
        screen.backend = self.backend
        if key not in self._user_screens:
            self._user_screens[key] = screen
            self._enforce_limits()
            await screen.on_command(args if args is not None else [], update)
        if not_initiated:
            await screen.display(update)
        return screen

    async def remove_current_screen(self, update: TuicanUpdate):
        try:
            user_id = get_user_id(update)
        except UserNotFoundError:
            return
        command = self._get_user_command(update)
        if command is None:
            return
        key = (command, user_id)
        if key in self._user_screens:
            del self._user_screens[key]
        await self._remove_user_command(update)

    def _get_user_command(self, update: TuicanUpdate) -> str | None:
        user_id = get_user_id(update)
        return self._user_commands.get(user_id)

    async def _set_user_command(self, update: TuicanUpdate, command: str):
        user_id = get_user_id(update)
        self._user_commands[user_id] = command
        self._enforce_limits()
        await self._state_store.save(user_id, command)

    async def _remove_user_command(self, update: TuicanUpdate):
        user_id = get_user_id(update)
        if user_id in self._user_commands:
            del self._user_commands[user_id]
        await self._state_store.delete(user_id)
