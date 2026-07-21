import inspect
from typing import Any

from .button import Button
from .component import CallBack, Component, _invoke_callback
from .input import Input


class Form:
    """Multi-input form with a submit button.

    Groups Input fields and validates them on submit.

    Example:
        self.form = Form(
            inputs=[
                Input[str](text="Name", validation_function=lambda x: x),
                Input[int](text="Age", validation_function=positive_int),
            ],
            on_submit=self.on_submit,
        )
        super().__init__(self.form.components)

        def get_layout(self):
            return self.form.get_layout()

        async def on_submit(self, form):
            values = form.values
            print(values)  # {"Name": "John", "Age": 30}
    """

    def __init__(
        self,
        inputs: list[Input[Any]],
        on_submit: CallBack | None = None,
        submit_text: str = "Submit",
    ):
        self._inputs = list(inputs)
        self._on_submit = on_submit
        self._submit_btn = Button(submit_text, on_change=self._submit)

    async def _submit(self) -> None:
        if self._on_submit:
            result = _invoke_callback(self._on_submit, None, self)
            if inspect.isawaitable(result):
                await result

    @property
    def inputs(self) -> list[Input[Any]]:
        return list(self._inputs)

    @property
    def values(self) -> dict[str, Any]:
        return {inp.text: inp.value for inp in self._inputs}

    def validate(self) -> list[str]:
        """Return list of validation error messages for inputs with no value."""
        errors: list[str] = []
        for inp in self._inputs:
            if inp.value is None:
                errors.append(f"{inp.text} is required")
        return errors

    @property
    def components(self) -> list[Component]:
        return self._inputs + [self._submit_btn]

    def get_layout(self) -> list[list[Component]]:
        rows: list[list[Component]] = []
        for inp in self._inputs:
            rows.append([inp])
        rows.append([self._submit_btn])
        return rows
