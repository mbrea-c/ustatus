import asyncio, gbulb, gi

gi.require_version("Gtk", "3.0")

try:
    gi.require_version("GtkLayerShell", "0.1")
except ValueError:
    import sys

    raise RuntimeError(
        "\n\n"
        + "If you haven't installed GTK Layer Shell, you need to point Python to the\n"
        + "library by setting GI_TYPELIB_PATH and LD_LIBRARY_PATH to <build-dir>/src/.\n"
        + "For example you might need to run:\n\n"
        + "GI_TYPELIB_PATH=build/src LD_LIBRARY_PATH=build/src python3 "
        + " ".join(sys.argv)
    )

from gi.repository import Gtk, GtkLayerShell
from pystatus.cpu_module import CpuModule
from pystatus.battery_module import BatteryModule
from pystatus.volume_module import VolumeModule


def main():
    application = Gtk.Application()
    application.connect("activate", lambda app: build_ui(app))
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    loop = asyncio.get_event_loop()
    loop.run_forever(application=application)


def build_ui(application):
    window = Gtk.Window(application=application)
    parent = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    top_level_grid = Gtk.Grid()
    top_level_grid.set_column_homogeneous(False)
    top_level_grid.set_row_homogeneous(False)
    label = Gtk.Label(label="Status")
    cpu_module = CpuModule()
    battery_module = BatteryModule()
    volume_module = VolumeModule()

    top_level_grid.attach(battery_module, 0, 0, 1, 1)
    top_level_grid.attach(volume_module, 0, 1, 1, 1)
    top_level_grid.attach(cpu_module, 1, 0, 1, 2)
    parent.add(label)
    parent.add(top_level_grid)
    window.add(parent)

    GtkLayerShell.init_for_window(window)
    # GtkLayerShell.auto_exclusive_zone_enable(window)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 10)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 10)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, 1)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)
    # Gtk.main()


if __name__ == "__main__":
    main()
