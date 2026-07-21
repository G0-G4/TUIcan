import inspect

from .button import Button
from .component import CallBack, Component, _invoke_callback
from .label import Label


class Stepper:
    """Numeric stepper with decrement, display, and increment buttons.

    Provides a [−] [value] [+] control row for adjusting a numeric value.

    Example:
        self.qty = Stepper(initial=1, min_value=1, max_value=10, on_change=self.on_qty_change)
        super().__init__(self.qty.components)

        def get_layout(self):
            return [[self.qty]] + self.qty.get_layout()
    """

    def __init__(
        self,
        initial: int = 0,
        min_value: int | None = None,
        max_value: int | None = None,
        step: int = 1,
        on_change: CallBack | None = None,
    ):
        self._value = initial
        self._min = min_value
        self._max = max_value
        self._step = step
        self._on_change = on_change
        self._dec_btn = Button("−", on_change=self._decrement)
        self._display = Label(str(self._value))
        self._inc_btn = Button("+", on_change=self._increment)

    async def _decrement(self) -> None:
        new_value = self._value - self._step
        if self._min is not None and new_value < self._min:
            return
        self._value = new_value
        self._display.text = str(self._value)
        if self._on_change:
            result = _invoke_callback(self._on_change, None, self)
            if inspect.isawaitable(result):
                await result

    async def _increment(self) -> None:
        new_value = self._value + self._step
        if self._max is not None and new_value > self._max:
            return
        self._value = new_value
        self._display.text = str(self._value)
        if self._on_change:
            result = _invoke_callback(self._on_change, None, self)
            if inspect.isawaitable(result):
                await result

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = val
        self._display.text = str(val)

    @property
    def components(self) -> list[Component]:
        return [self._dec_btn, self._display, self._inc_btn]

    def get_layout(self) -> list[list[Component]]:
        return [[self._dec_btn, self._display, self._inc_btn]]
