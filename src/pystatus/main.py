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
            init_service(lambda: self.hide(), lambda: self.show(), bar_name)
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
        # window.set_size_request(100, 100)
        # window.resize(100, 100)

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
                        VolumeModule(gtk_orientation=self.gtk_orientation)
                    )
                case "battery":
                    self.modules.append(
                        BatteryModule(gtk_orientation=self.gtk_orientation)
                    )
                case "mpris":
                    self.modules.append(
                        MprisModule(gtk_orientation=self.gtk_orientation)
                    )
                case "cpu":
                    self.modules.append(CpuModule(gtk_orientation=self.gtk_orientation))
                case "tray":
                    self.modules.append(
                        TrayModule(gtk_orientation=self.gtk_orientation)
                    )
                case other:
                    raise ConfigError(f"Module type {other} not defined.")
        for module in self.modules:
            self.box.add(module)


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
