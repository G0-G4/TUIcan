import pytest
from tuican.components.form import Form
from tuican.components.input import Input
from tuican.components.button import Button


class TestForm:
    def test_init(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        form = Form(inputs=[name_input])
        assert len(form.inputs) == 1
        assert isinstance(form.inputs[0], Input)

    def test_components_returns_inputs_plus_submit(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        age_input = Input[int](text="Age", validation_function=lambda x: int(x))
        form = Form(inputs=[name_input, age_input])
        comps = form.components
        assert len(comps) == 3
        assert isinstance(comps[0], Input)
        assert isinstance(comps[1], Input)
        assert isinstance(comps[2], Button)

    def test_get_layout(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        age_input = Input[int](text="Age", validation_function=lambda x: int(x))
        form = Form(inputs=[name_input, age_input])
        layout = form.get_layout()
        assert len(layout) == 3  # 2 inputs + 1 submit row
        assert layout[0] == [name_input]
        assert layout[1] == [age_input]
        assert layout[2] == [form._submit_btn]

    def test_values_property(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        name_input.value = "John"
        form = Form(inputs=[name_input])
        assert form.values == {"Name": "John"}

    def test_values_with_none(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        form = Form(inputs=[name_input])
        assert form.values == {"Name": None}

    def test_validate_empty(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        form = Form(inputs=[name_input])
        errors = form.validate()
        assert errors == ["Name is required"]

    def test_validate_filled(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        name_input.value = "John"
        form = Form(inputs=[name_input])
        assert form.validate() == []

    def test_validate_multiple_errors(self):
        name_input = Input[str](text="Name", validation_function=lambda x: x)
        age_input = Input[int](text="Age", validation_function=lambda x: int(x))
        form = Form(inputs=[name_input, age_input])
        errors = form.validate()
        assert len(errors) == 2
        assert "Name is required" in errors
        assert "Age is required" in errors

    def test_custom_submit_text(self):
        form = Form(inputs=[], submit_text="Send")
        assert form._submit_btn.text == "Send"

    @pytest.mark.asyncio
    async def test_submit_triggers_on_submit(self, mock_screen):
        handler_called = False
        received = None

        async def handler(component):
            nonlocal handler_called, received
            handler_called = True
            received = component

        form = Form(inputs=[], on_submit=handler)
        form._submit_btn.parent_screen = mock_screen
        await form._submit_btn.click()
        assert handler_called is True
        assert received is form
