from typing import Callable
from gi.repository import Gtk, GLib
from ustatus.config import ModuleConfig
from ustatus.graphics.battery import Battery
from ustatus.module import Module
import psutil


class BatteryModule(Module):
    def __init__(
        self,
        update_period_seconds=3,
        **kwargs,
    ) -> None:
        module_widget = BatteryWidget()
        super().__init__(module_widget=module_widget, **kwargs)

        self._update()
        GLib.timeout_add(update_period_seconds * 1000, lambda: self._update())

    def _update(self) -> bool:
        self.module_widget.update()
        return True


class BatteryWidget(Gtk.Box):
    def __init__(self):
        super().__init__()
        grid = Gtk.Grid()
        grid.set_column_homogeneous(False)
        grid.set_row_homogeneous(False)
        self.battery = Battery(charge=0.4, ac=True)
        self.battery.set_size_request(25, 25)
        self.charge_label = Gtk.Label()

        grid.attach(self.battery, 0, 0, 1, 1)
        grid.attach(self.charge_label, 1, 0, 1, 1)

        self.set_center_widget(grid)

    def update(self):
        battery_data = psutil.sensors_battery()
        self.battery.update(
            charge=battery_data.percent / 100, ac=battery_data.power_plugged
        )
        self.charge_label.set_label(f"{battery_data.percent:.0f}%")
