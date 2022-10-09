from typing import Callable, Optional
from gi.repository import Gtk, GLib
from python_reactive_ui import Component
from python_reactive_ui.backends.gtk3.builtin.box import Box
from python_reactive_ui.backends.gtk3.builtin.label import Label

from ustatus.config import ModuleConfig


class ReactiveModule(Component):
    def _render(self, props, children):
        module_config = props["module_config"]
        match children:
            case [child]:
                return Box(
                    {"css_classes": "module", "orientation": "vertical"},
                    [
                        *(
                            (Label({"text": module_config.label}),)
                            if module_config.show_label
                            else ()
                        ),
                        child,
                    ],
                )
            case _:
                return ValueError("Only a single child allowed")
