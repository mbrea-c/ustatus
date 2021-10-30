from gi.repository import Gtk, GLib
from pystatus.battery import Battery
import psutil


class BatteryModule(Gtk.Frame):
    def __init__(self, update_period_seconds = 3) -> None:
        super().__init__()
        grid = Gtk.Grid()
        grid.set_column_homogeneous(False)
        grid.set_row_homogeneous(False)
        label = Gtk.Label(label="Battery")
        self.battery = Battery(charge=0.4, ac=True)
        self.battery.set_size_request(40, 40)
        self.charge_label = Gtk.Label()

        grid.attach(label, 0, 0, 2, 1)
        grid.attach(self.battery, 0, 1, 1, 1)
        grid.attach(self.charge_label, 1,1,1,1)
        self.add(grid)

        self.update()
        GLib.timeout_add(update_period_seconds * 1000, lambda: self.update())

    def update(self) -> bool:
        battery_data = psutil.sensors_battery()
        self.battery.update(charge=battery_data.percent/100, ac=battery_data.power_plugged)
        self.charge_label.set_label(f"{battery_data.percent:.0f}%")
        return True
