from time import localtime, strftime
from typing import Callable
from python_reactive_ui import Component, use_state
from python_reactive_ui.backends.gtk3.builtin.label import Label
from ustatus.hooks.use_timer import use_timer


class Clock(Component):
    def _update_time(self, set_time: Callable):
        set_time(localtime())

    def _render(self, props, children):
        time, set_time = use_state(self, localtime())
        handle = use_timer(self, 1, lambda: self._update_time(set_time))
        return Label({"text": strftime("%H:%M:%S", time), "hexpand": True})
