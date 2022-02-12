import asyncio, gbulb, gi, argparse, logging, logging.handlers

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
from pystatus.remote_service import init_service
from pystatus.config import Config, ConfigError
from pystatus.modules.battery_module import BatteryModule
from pystatus.modules.cpu_module import CpuModule
from pystatus.modules.mpris_module import MprisModule
from pystatus.modules.tray_module import TrayModule
from pystatus.modules.volume_module import VolumeModule


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Start a pystatus instance of the bar of given name."
    )
    parser.add_argument(
        "bar_name",
        metavar="bar",
        type=str,
        help="name of the bar to spawn",
    )
    args = parser.parse_args()
    bar_name = args.bar_name
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    application = Gtk.Application()
    application.connect("activate", lambda app: build_ui(app, bar_name))
    loop = asyncio.get_event_loop()
    loop.run_forever(application=application)


def build_ui(application, bar_name):
    config = Config()
    pystatus = Pystatus(application, bar_name, config)


class Pystatus(Gtk.Window):
    def __init__(self, application: Gtk.Application, bar_name: str, config: Config):
        super().__init__(application=application)

        self.config = config
        self.modal_window = Gtk.Window(application=application)
        self.modal_widget = None
        self.bar_name = bar_name
        self.box = Gtk.Box()
        self.config_box()
        setup_module_css()

        modules = self.instantiate_modules()

        self.add(self.box)

        self.setup_layer_shell()

        self.show_all()
        self.connect("destroy", Gtk.main_quit)

        asyncio.create_task(
            init_service(
                lambda: self.hide_status(), lambda: self.show_status(), bar_name
            )
        )

    def setup_layer_shell(self):
        GtkLayerShell.init_for_window(self)
        for anchor in self.config.get_entry_for_bar(self.bar_name, "anchors"):
            match anchor:
                case "right":
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
                case "left":
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
                case "top":
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
                case "bottom":
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 1)
                case _:
                    raise ConfigError(f"Anchor point {anchor} not defined.")
        GtkLayerShell.init_for_window(self.modal_window)
        self.update_modal_anchor()
        self.connect("size-allocate", lambda window, size: self.update_modal_anchor())
        # window.set_size_request(100, 100)
        # window.resize(100, 100)

    def show_status(self):
        self.show()

    def hide_status(self):
        self.hide_modal()
        self.hide()

    def show_modal(self, widget: Gtk.Widget):
        if self.modal_widget:
            self.modal_window.remove(self.modal_widget)
        self.modal_widget = widget
        self.modal_window.add(self.modal_widget)
        self.modal_window.show_all()

    def hide_modal(self):
        if self.modal_widget:
            self.modal_window.remove(self.modal_widget)
            self.modal_widget = None
        self.modal_window.hide()

    def toggle_modal(self, widget: Gtk.Widget):
        if self.modal_widget == widget:
            self.hide_modal()
        else:
            self.show_modal(widget)

    def config_box(self):
        match self.config.get_entry_for_bar(self.bar_name, "orientation"):
            case "horizontal":
                self.gtk_orientation = Gtk.Orientation.HORIZONTAL
                self.box.set_orientation(self.gtk_orientation)
            case "vertical":
                self.gtk_orientation = Gtk.Orientation.VERTICAL
                self.box.set_orientation(self.gtk_orientation)
            case other:
                raise ConfigError(f"Orientation {other} not defined.")

    def instantiate_modules(self):
        module_names = self.config.get_entry_for_bar(self.bar_name, "modules")

        self.modules = []
        for module_name in module_names:
            match self.config.get_entry_for_module(module_name, "type"):
                case "volume":
                    self.modules.append(
                        VolumeModule(
                            gtk_orientation=self.gtk_orientation,
                            toggle_modal=self.toggle_modal,
                        )
                    )
                case "battery":
                    self.modules.append(
                        BatteryModule(
                            gtk_orientation=self.gtk_orientation,
                            toggle_modal=self.toggle_modal,
                        )
                    )
                case "mpris":
                    self.modules.append(
                        MprisModule(
                            gtk_orientation=self.gtk_orientation,
                            toggle_modal=self.toggle_modal,
                        )
                    )
                case "cpu":
                    self.modules.append(
                        CpuModule(
                            gtk_orientation=self.gtk_orientation,
                            toggle_modal=self.toggle_modal,
                        )
                    )
                case "tray":
                    self.modules.append(
                        TrayModule(
                            gtk_orientation=self.gtk_orientation,
                            toggle_modal=self.toggle_modal,
                        )
                    )
                case other:
                    raise ConfigError(f"Module type {other} not defined.")
        for module in self.modules:
            self.box.add(module)

    def update_modal_anchor(self):
        margin_x = 1
        margin_y = 1
        match self.gtk_orientation:
            case Gtk.Orientation.VERTICAL:
                margin_x = self.get_allocated_width()
                margin_y = 1
            case Gtk.Orientation.HORIZONTAL:
                margin_y = self.get_allocated_height()
                margin_x = 1
        for anchor in self.config.get_entry_for_bar(self.bar_name, "anchors"):
            match anchor:
                case "right":
                    GtkLayerShell.set_anchor(
                        self.modal_window, GtkLayerShell.Edge.RIGHT, True
                    )
                    GtkLayerShell.set_margin(
                        self.modal_window, GtkLayerShell.Edge.RIGHT, margin_x
                    )
                case "left":
                    GtkLayerShell.set_anchor(
                        self.modal_window, GtkLayerShell.Edge.LEFT, True
                    )
                    GtkLayerShell.set_margin(
                        self.modal_window, GtkLayerShell.Edge.LEFT, margin_x
                    )
                case "top":
                    GtkLayerShell.set_anchor(
                        self.modal_window, GtkLayerShell.Edge.TOP, True
                    )
                    GtkLayerShell.set_margin(
                        self.modal_window, GtkLayerShell.Edge.TOP, margin_y
                    )
                case "bottom":
                    GtkLayerShell.set_anchor(
                        self.modal_window, GtkLayerShell.Edge.BOTTOM, True
                    )
                    GtkLayerShell.set_margin(
                        self.modal_window, GtkLayerShell.Edge.BOTTOM, margin_y
                    )
                case _:
                    raise ConfigError(f"Anchor point {anchor} not defined.")


def setup_module_css():
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    provider.load_from_data(".module-button {padding: 0;}".encode())


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="[{levelname}({name}):{filename}:{funcName}] {message}",
    )
    root_logger = logging.getLogger()
    sys_handler = logging.handlers.SysLogHandler(address="/dev/log")
    root_logger.addHandler(sys_handler)


if __name__ == "__main__":
    main()
