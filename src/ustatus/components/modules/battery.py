from collections import namedtuple
from gi.repository import Gtk
from python_reactive_ui import Component, use_state
from python_reactive_ui.backends.gtk3.builtin.box import Box
from python_reactive_ui.backends.gtk3.builtin.label import Label
from ustatus.components.drawing.battery_icon import BatteryIcon
from ustatus.hooks.use_timer import use_timer
import psutil


class Battery(Component):
    BatteryData = namedtuple("BatteryData", ["charge", "ac"])

    @classmethod
    def _get_data(cls):
        battery_data = psutil.sensors_battery()
        return (
            cls.BatteryData(
                charge=battery_data.percent / 100, ac=battery_data.power_plugged
            )
            if battery_data
            else cls.BatteryData(charge=0, ac=True)
        )

    def _render(self, props, children):
        data, set_data = use_state(self, Battery._get_data())
        use_timer(
            self,
            timer_secs=5,
            repeat=True,
            callback=lambda: set_data(Battery._get_data()),
        )
        return Box(
            { "halign": "center", "hexpand": True },
            [
                BatteryIcon(
                    {"charge": data.charge, "ac": data.ac, "size_request": (25, 25)}
                ),
                Label({"text": f"{data.charge * 100:.0f}%"}),
            ],
        )
