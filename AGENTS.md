# AGENTS.md — TUIcan

## Project Overview

TUIcan is a Python library for building interactive Telegram bot interfaces with reusable UI components. It is built on top of `python-telegram-bot` and follows a component-based architecture inspired by frontend frameworks.

## Architecture

### Entry Point: `Application` (`src/tuican/application.py`)

- Stores per-user state (`_user_commands`, `_user_screens`) keyed by `(command, user_id)`.
- Routes Telegram updates to the correct `Screen` instance.
- Supports middleware pipeline (`@app.middleware`), persistence (`StateStore`), and two run modes (`run_polling`, `run_webhook`).
- All user-facing handlers (`command_handler`, `dispatcher`, `message_dispatcher`) run middleware first. Return `False` from any middleware to abort processing.

### Backend Abstraction (`src/tuican/backend.py`)

- `MessageBackend` protocol abstracts all Telegram API calls.
- `PythonTelegramBotBackend` is the default implementation.
- `Application` creates one backend instance and injects it into every `Screen` via `screen.backend = ...`.

### Screen & Component System (`src/tuican/components/`)

- **`Component`** base class: every UI element has `component_id`, `callback_data`, `on_change`, and lifecycle methods `render()`, `handle_callback()`.
- **`MessageHandlingComponent`** extends `Component` for elements that accept text messages (e.g., `Input`).
- **`Screen`** is the layout container:
  - `get_layout()` returns `Sequence[Sequence[InlineKeyboardButton | Component]]`.
  - `display()` auto-calls `render()` on any `Component` items, so users do **not** need to call `render()` manually.
  - `dispatcher()` routes callback queries to the correct component via `ComponentRegistry._callback_map`.
- **`ComponentRegistry`** (`src/tuican/components/screen.py`) handles component registration, callback dispatching, and input focus management. `Screen` delegates to it.
- **`ScreenGroup`** is a stack-based screen navigator. It proxies all methods to the top screen on its stack. New screens pushed via `go_to_screen()` automatically inherit the parent's `backend`.

### State Persistence (`src/tuican/state_store.py`)

- `StateStore` protocol with three methods: `load`, `save`, `delete`.
- `InMemoryStateStore` (default, volatile).
- `JsonFileStateStore` (survives restarts, sync disk I/O).
- `Application` loads all persisted commands at startup (`post_init` wrapper) and writes on every `_set_user_command` / `_remove_user_command`.

### Validation (`src/tuican/validation/`)

- Simple validators (e.g., `positive_int`, `positive_float`) that raise `ValidationError` on invalid input.
- `ValidationError` is caught specially in `Application.message_dispatcher` so the error message is shown to the user without stopping the bot.

## Key Patterns

### Callback Routing

Components are identified by `callback_data` (falls back to `component_id`). `Screen` maintains `_callback_map: dict[str, Component]`. When a user taps an inline button, Telegram sends the `callback_data`; `Screen.dispatcher()` looks it up and calls `component.handle_callback()`.

### Input Focus

Only one `MessageHandlingComponent` may be active at a time per screen. `Input.toggle()` / `Input.activate()` call `Screen.set_focus()`, which deactivates the previously focused input via `ComponentRegistry`.

### Lifecycle

1. User sends `/start` → `Application.command_handler()` removes old screen, sets command, creates screen, calls `screen.start_handler()` → `screen.display()`.
2. User taps a button → `Application.dispatcher()` gets or creates screen, calls `screen.dispatcher()` → component updates state → if `True`, `screen.display()` refreshes the message.
3. User sends text while an input is active → `Application.message_dispatcher()` routes to `screen.message_dispatcher()` → input validates and stores value → screen redisplays.

## File Layout

```
src/tuican/
  __init__.py           # re-exports Application, get_user_id
  application.py        # Application, middleware, routing
  backend.py            # MessageBackend protocol + default impl
  state_store.py        # StateStore protocol + default impl
  errors/
    __init__.py         # ValidationError
  validation/
    __init__.py         # positive_int, positive_float, etc.
  components/
    __init__.py         # re-exports all public components
    component.py        # Component, MessageHandlingComponent, CallBack
    screen.py           # Screen, ScreenGroup, ComponentRegistry, StartScreenProtocol
    button.py
    checkbox.py
    input.py
    hline.py
```

## Type Checking

- Project uses **mypy** for static type analysis.
- Run with: `/Users/g.grishenkov/projects/TUIcan/.venv/bin/python -m mypy src/tuican/ --show-error-codes`
- Config is in `pyproject.toml` under `[tool.mypy]`. We keep it practical: catches real type bugs without forcing annotations on every function.
- **Never** suppress type errors (`as any`, `@ts-ignore`). If a type error is hard to fix, refactor the code instead.

## Testing

- Run with: `/Users/g.grishenkov/projects/TUIcan/.venv/bin/python -m pytest tests/ -v`
- 70 unit tests covering component state, rendering, callback handling, focus management.
- Tests use `unittest.mock.MagicMock` / `AsyncMock` for Telegram objects.
- Python 3.13+ required (uses `class Input[T]` generic syntax).

## Constraints for Agents

- **Never** suppress type errors (`as any`, `@ts-ignore`).
- **Never** delete failing tests to make CI green.
- **Never** commit without explicit user request.
- **Never** leave code in a broken state.
- Prefer `logging.getLogger(__name__)` over `print()`.
- Keep `Screen` backward compatible: `get_layout()` should still accept `InlineKeyboardButton` objects directly.
- Any new component must subclass `Component` and implement `render()` and `handle_callback()`.
