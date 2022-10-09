from python_reactive_ui import Component
from python_reactive_ui.backends.gtk3.builtin.label import Label


class Test(Component):
    def _render(self, props, children):
        return Label({"text": "Testing..."})
