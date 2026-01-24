# TUIcan - Telegram UI Components

![](./images/TUIcan.png)

A Python library for building interactive Telegram bot interfaces with reusable UI components.

## Features

- 🏗️ Modular UI components (Buttons, Checkboxes, Input fields)
- 🖥️ Screen management with navigation support
- ♻️ Stateful components with change callbacks
- 📱 Message and callback query handling built-in

## Installation

```bash
pip install TUIcan
```

Or for development:
```bash
git clone https://github.com/yourusername/TUIcan.git
cd TUIcan
pip install -e .
```

## Quick Start

1. Create a `.env` file with your bot token:
```bash
echo "token=YOUR_BOT_TOKEN" > .env
```

2. Create a simple button screen:
```python
from src.tuican.application import Application
from src.tuican.components import Button, Screen

class MyScreen(Screen):
    def __init__(self):
        self.button = Button("Click me", on_change=self.handle_click)
        super().__init__([self.button], message="Welcome!")

    def handle_click(self, update, context, callback_data, component):
        self.message = "Button clicked!"

    def get_layout(self, update, context):
        return [[self.button.render(update, context)]]

app = Application("YOUR_BOT_TOKEN", MyScreen)
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
Validated input field:
```python
Input[int](text="Age:", validation_function=positive_int)
```

### Screen Management
- `Screen`: Base container for components
- `ScreenGroup`: Handles navigation between screens

## API Reference

### Application
Main entry point:
```python
Application(token, main_screen_factory)
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

- Python 3.10+
- python-telegram-bot
- python-dotenv

## License

MIT

