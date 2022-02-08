from gi.repository import Gtk, GLib
from pystatus.graphics.battery import Battery
from pystatus.module import ModuleWithModal
import psutil


class BatteryModule(ModuleWithModal):
    def __init__(
        self, gtk_orientation: Gtk.Orientation, update_period_seconds=3
    ) -> None:
        module_widget = BatteryWidget()
        modal_widget = BatteryWidget()
        super().__init__(
            module_widget=module_widget,
            modal_widget=modal_widget,
            gtk_orientation=gtk_orientation,
        )

        self._update()
        GLib.timeout_add(update_period_seconds * 1000, lambda: self._update())

        self._update_modal()
        GLib.timeout_add(update_period_seconds * 1000, lambda: self._update_modal())

    def _update(self) -> bool:
        self.module_widget.update()
        return True

    def _update_modal(self) -> bool:
        self.modal_widget.update()
        return True


class BatteryWidget(Gtk.Grid):
    def __init__(self):
        super().__init__()
        self.set_column_homogeneous(False)
        self.set_row_homogeneous(False)
        label = Gtk.Label(label="Battery")
        self.battery = Battery(charge=0.4, ac=True)
        self.battery.set_size_request(40, 40)
        self.charge_label = Gtk.Label()

        self.attach(label, 0, 0, 2, 1)
        self.attach(self.battery, 0, 1, 1, 1)
        self.attach(self.charge_label, 1, 1, 1, 1)

    def update(self):
        battery_data = psutil.sensors_battery()
        self.battery.update(
            charge=battery_data.percent / 100, ac=battery_data.power_plugged
        )
        self.charge_label.set_label(f"{battery_data.percent:.0f}%")


class BatteryModalWidget:
    pass
