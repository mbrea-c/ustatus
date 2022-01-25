import asyncio, gbulb, gi

gi.require_version("Gtk", "3.0")
gi.require_version("DbusmenuGtk3", "0.4")

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

from gi.repository import Gtk, GtkLayerShell, Gdk
from pystatus.modules.cpu_module import CpuModule
from pystatus.modules.battery_module import BatteryModule
from pystatus.modules.volume_module import VolumeModule
from pystatus.modules.tray_module import TrayModule
from pystatus.remote_service import init_service


def main():
    application = Gtk.Application()
    application.connect("activate", lambda app: build_ui(app))
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    loop = asyncio.get_event_loop()
    loop.run_forever(application=application)


def build_ui(application):
    window = Gtk.Window(application=application)
    parent = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label = Gtk.Label(label="Status")
    setup_module_css()
    cpu_module = CpuModule()
    battery_module = BatteryModule()
    volume_module = VolumeModule()
    tray_module = TrayModule()

    parent.add(label)
    parent.add(battery_module)
    parent.add(volume_module)
    parent.add(cpu_module)
    parent.add(tray_module)
    window.add(parent)

    GtkLayerShell.init_for_window(window)
    # GtkLayerShell.auto_exclusive_zone_enable(window)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 10)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 10)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, 1)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)

    print("About to run create task")
    asyncio.create_task(init_service(lambda: window.hide(), lambda: window.show()))


def setup_module_css():
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    provider.load_from_data(".module-button {padding: 0;}".encode())


if __name__ == "__main__":
    main()
