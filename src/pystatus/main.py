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
from pystatus.config import instantiate_modules_for_bar, read_config


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
    application = Gtk.Application()
    application.connect("activate", lambda app: build_ui(app, bar_name))
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    loop = asyncio.get_event_loop()
    loop.run_forever(application=application)


def build_ui(application, bar_name):
    window = Gtk.Window(application=application)
    parent = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label = Gtk.Label(label="Status")
    setup_module_css()

    config = read_config()

    modules = instantiate_modules_for_bar(bar_name, config)

    parent.add(label)

    for module in modules:
        parent.add(module)
    window.add(parent)

    GtkLayerShell.init_for_window(window)
    # GtkLayerShell.auto_exclusive_zone_enable(window)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 10)
    # GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 10)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, 1)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)

    asyncio.create_task(
        init_service(lambda: window.hide(), lambda: window.show(), bar_name)
    )


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
