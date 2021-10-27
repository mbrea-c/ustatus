import gi

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


def main():
    window = Gtk.Window()
    top_level_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label = Gtk.Label(label="Status")
    cpu_module = CpuModule()

    top_level_box.add(label)
    top_level_box.add(cpu_module)
    window.add(top_level_box)

    GtkLayerShell.init_for_window(window)
    # GtkLayerShell.auto_exclusive_zone_enable(window)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 10)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 10)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, 1)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()
