# TUIcan - Toolkit for User Intuitive Chat Application Navigation

**Under development, possible breaking changes!**

<img src="./images/TUIcan.png" width="256">

A Python library for building interactive Telegram bot interfaces with reusable UI components.


## Features

- 🏗️ Modular UI components (Buttons, Checkboxes, Input fields)
- 🖥️ Screen management with navigation support
- ♻️ Stateful components with change callbacks
- 📱 Message and callback query handling built-in
- 🔄 Declarative layout (no manual `render()` calls)
- 🛡️ Middleware pipeline for cross-cutting concerns
- 💾 Pluggable persistence (in-memory or JSON file)
- 🌐 Webhook or polling mode

## Adding to project

```bash
uv add "tuican @ git+https://github.com/G0-G4/TUIcan.git"
```

## Quick Start

1. Create a `.env` file with your bot token:
```bash
echo "token=YOUR_BOT_TOKEN" > .env
```

2. Create a simple button screen:
```python
import os

from dotenv import load_dotenv

from src.tuican.application import Application
from src.tuican.components import Button, Screen

class MyScreen(Screen):
    description = 'main screen'
    def __init__(self):
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="click the button")

    def handle_click(self, update, context, component):
        self.message = "Hello world!"

    async def get_layout(self, update, context):
        return [[self.button]]  # declarative: no manual render() needed

load_dotenv()
token = os.getenv("token")
app = Application(token, {'start': MyScreen})
app.run()
```

## Core Components

### Button
Basic interactive button with click handler:
```python
Button(text="Click me", on_change=callback_function)
```

### CheckBox
Toggleable checkbox with group support:
```python
group = ExclusiveCheckBoxGroup()
CheckBox(text="Option 1", group=group)
```

### Input
Validated input field with configurable prompt:
```python
Input[int](
    text="Age:",
    validation_function=positive_int,
    active_prompt="Enter: "   # shown when input is active
)
```

### Screen Management
- `Screen`: Base container for components
- `ScreenGroup`: Handles navigation between screens

## Declarative Layout

`Screen.get_layout()` can return components directly. The library automatically calls `render()` for you:

```python
async def get_layout(self, update, context):
    return [
        [self.btn1, self.btn2],           # row 1
        [self.checkbox],                  # row 2
        [self.input_field],               # row 3
    ]
```

You can still mix pre-rendered `KeyboardButton` objects if needed.

## Middleware

Register middleware to handle cross-cutting concerns like auth or rate limiting:

```python
@app.middleware
async def auth_middleware(update, context):
    user_id = get_user_id(update)
    if user_id not in ALLOWED_USERS:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Access denied"
        )
        return False
    return True
```

Return `False` to stop processing the update.

## Persistence

User command state is persisted automatically. By default an in-memory store is used (lost on restart). Use `JsonFileStateStore` to survive restarts:

```python
from tuican.state_store import JsonFileStateStore

app = Application(
    token,
    {'start': MyScreen},
    state_store=JsonFileStateStore("bot_state.json")
)
```

## Webhook Mode

Run the bot in webhook mode instead of polling:

```python
app.run_webhook(
    webhook_url="https://your-domain.com/webhook",
    listen="0.0.0.0",
    port=8080
)
```

## Custom Backend

The Telegram API is abstracted behind the `MessageBackend` protocol. You can provide a custom backend for testing or integrating with a different Telegram library:

```python
from tuican.backend import MessageBackend

class MyBackend(MessageBackend):
    async def send_keyboard_message(self, update, context, text, keyboard_markup, parse_mode="HTML"):
        ...

app = Application(token, screens)
app._backend = MyBackend()
```

## API Reference

### Application
Main entry point:
```python
Application(token, screens: dict[str, StartScreenProtocol], state_store=None)
```

### Component
Base class with:
- `handle_callback()` - Process button clicks
- `render()` - Create Telegram button
- `call_on_change()` - Trigger callbacks

## Examples

See the `examples/` directory for:
- `press_counter.py` - Simple button counter
- `components_showcase.py` - All component types demo
- `multiple_screens.py` - Screen navigation example

## Requirements

- Python 3.13+
- python-telegram-bot
- python-dotenv

## License

MIT
