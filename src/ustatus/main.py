import asyncio, gbulb, gi, logging, logging.handlers, os
from ustatus.utils.swaymsg import get_outputs
import inspect


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

from gi.repository import Gtk, GtkLayerShell, Gdk, Notify
from ustatus.remote_service import init_service
from ustatus.config import BarConfig, Config, ConfigError, ModuleConfig
from ustatus.modules.battery_module import BatteryModule
from ustatus.modules.cpu_module import CpuModule
from ustatus.modules.mpris_module import MprisModule
from ustatus.modules.tray_module import TrayModule
from ustatus.modules.volume_module import VolumeModule
from ustatus.modules.sway_module import SwayModule
from ustatus.modules.power_profiles_module import PowerProfilesModule
from ustatus.modules.power_module import PowerModule
from ustatus.utils.notifications import notify_error


def main():
    setup_logging()
    config = Config()
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    application = Gtk.Application()
    application.connect(
        "activate",
        lambda app: build_ui(application=app, config=config),
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever(application=application)
    except Exception as e:
        notify_error(summary="Uncaught error", body=f"e")


def build_ui(application, config):
    ustatus = Ustatus(application=application, config=config)


class Ustatus(Gtk.Window):
    def __init__(
        self,
        application: Gtk.Application,
        config: Config,
    ):
        super().__init__(application=application)
        bar_name = config.bar_name
        output = config.config_dict["bars"][bar_name].get("output", None)
        Notify.init(f"ustatus {bar_name}")

        self.config: Config = config
        self.bar_config: BarConfig = self.config.get_bar_config(bar_name)
        self.modal_window = Gtk.Window(application=application)
        self.modal_widget = None
        self.bar_name = bar_name
        self.output = output

        self._setup_gtk_theme()
        self._setup_css_classes()

        self._init_box()
        self._init_layer_shell()
        setup_css()
        self._init_modules()

        self.center_box.show_all()
        self.box.show_all()
        self.show_all()

        self.connect("destroy", Gtk.main_quit)

        asyncio.create_task(
            init_service(
                lambda: self.hide_status(), lambda: self.show_status(), bar_name
            )
        )

        if self.output:
            asyncio.create_task(self._move_to_monitor())

        logging.info(f"Initialized bar {bar_name}")

    def _setup_gtk_theme(self):
        if self.bar_config.theme_override is not None:
            logging.info(
                f"Overriding default theme with {self.bar_config.theme_override}"
            )
            Gtk.Settings.get_default().set_property(
                "gtk_theme_name", self.bar_config.theme_override
            )

    def _setup_css_classes(self):
        style_context = self.get_style_context()
        style_context.add_class(self.bar_name)
        style_context.add_class("ustatus")

        modal_style_context = self.modal_window.get_style_context()
        modal_style_context.add_class(self.bar_name)
        modal_style_context.add_class("ustatus")
        modal_style_context.add_class("modal")

    async def _move_to_monitor(self):
        monitor = await self._get_gdk_monitor(self.output)
        GtkLayerShell.set_monitor(self, monitor)

    async def _get_gdk_monitor(self, output):
        outputs = await get_outputs()
        out = list(filter(lambda m: m["name"] == output, outputs))
        assert len(out) == 1
        out = out[0]

        display = self.get_display()
        for num in range(display.get_n_monitors()):
            m = display.get_monitor(num)
            if m.get_model() == out["model"]:
                return m

        raise Exception(f"Could not find monitor {out}")

    def _init_layer_shell(self):
        GtkLayerShell.init_for_window(self)
        for anchor in self.bar_config.anchors:
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
        if self.bar_config.exclusive:
            self._update_exclusive_zone()
            self.connect(
                "size-allocate", lambda window, size: self._update_exclusive_zone()
            )

    def _init_modules(self):
        self.modules_start = self.instantiate_modules(self.bar_config.modules_start)
        self.modules_center = self.instantiate_modules(self.bar_config.modules_center)
        self.modules_end = self.instantiate_modules(
            reversed(self.bar_config.modules_end)
        )

        for module in self.modules_start:
            self.box.pack_start(child=module, expand=False, fill=False, padding=0)
        for module in self.modules_center:
            self.center_box.pack_start(
                child=module, expand=False, fill=False, padding=0
            )
        for module in self.modules_end:
            self.box.pack_end(child=module, expand=False, fill=False, padding=0)

    def show_status(self):
        self.show()

    def hide_status(self):
        self.hide_modal()
        self.hide()

    def show_modal(self, widget: Gtk.Widget):
        if self.modal_widget:
            self.modal_window.remove(self.modal_widget)
        self.modal_widget = widget
        self.modal_widget.get_style_context().add_class("modal-widget")
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

    def _init_box(self):
        self.scrolled_window_container = Gtk.ScrolledWindow.new()
        self.add(self.scrolled_window_container)
        self.box = Gtk.Box()
        self.box.set_vexpand(True)
        self.center_box = Gtk.Box()
        self.box.set_center_widget(self.center_box)
        if self.bar_config.width == "auto":
            h_scroll_policy = Gtk.PolicyType.NEVER
        else:
            h_scroll_policy = Gtk.PolicyType.EXTERNAL
            self.scrolled_window_container.set_max_content_width(self.bar_config.width)
            self.scrolled_window_container.set_min_content_width(self.bar_config.width)

        if self.bar_config.height == "auto":
            v_scroll_policy = Gtk.PolicyType.NEVER
        else:
            v_scroll_policy = Gtk.PolicyType.EXTERNAL
            self.scrolled_window_container.set_max_content_height(
                self.bar_config.height
            )
            self.scrolled_window_container.set_min_content_height(
                self.bar_config.height
            )

        self.scrolled_window_container.set_policy(h_scroll_policy, v_scroll_policy)

        match self.bar_config.orientation:
            case "horizontal":
                self.gtk_orientation = Gtk.Orientation.HORIZONTAL
                self.box.set_orientation(self.gtk_orientation)
                self.center_box.set_orientation(self.gtk_orientation)
            case "vertical":
                self.gtk_orientation = Gtk.Orientation.VERTICAL
                self.box.set_orientation(self.gtk_orientation)
                self.center_box.set_orientation(self.gtk_orientation)
            case other:
                raise ConfigError(f"Orientation {other} not defined.")
        self.scrolled_window_container.add(self.box)

    def instantiate_modules(self, module_names):
        modules = []
        for module_name in module_names:
            module_config = self.config.get_module_config(module_name)
            modules.append(
                create_builtin_module(
                    module_config=module_config,
                    bar_config=self.bar_config,
                    gtk_orientation=self.gtk_orientation,
                    toggle_modal=self.toggle_modal,
                    output=self.output,
                    bar_width=self.bar_config.width,
                )
            )
            if self.bar_config.separators:
                modules.append(Gtk.Separator.new(orientation=self._not_orientation()))
        return modules

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
        for anchor in self.bar_config.anchors:
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

    def _update_exclusive_zone(self):
        match self.gtk_orientation:
            case Gtk.Orientation.VERTICAL:
                margin = self.get_allocated_width()
            case Gtk.Orientation.HORIZONTAL:
                margin = self.get_allocated_height()
            case other:
                raise Exception(f"Orientation {other} not recognized")
        GtkLayerShell.set_exclusive_zone(self, margin)

    def _not_orientation(self):
        match self.gtk_orientation:
            case Gtk.Orientation.VERTICAL:
                return Gtk.Orientation.HORIZONTAL
            case Gtk.Orientation.HORIZONTAL:
                return Gtk.Orientation.VERTICAL
            case other:
                raise Exception(f"Orientation {other} not recognized")


def create_builtin_module(module_config: ModuleConfig, bar_config: BarConfig, **kwargs):
    builtins = {
        "volume": VolumeModule,
        "battery": BatteryModule,
        "mpris": MprisModule,
        "cpu": CpuModule,
        "tray": TrayModule,
        "sway": SwayModule,
        "power_profiles": PowerProfilesModule,
        "power": PowerModule,
    }
    if module_config.type in builtins:
        return builtins[module_config.type](config=module_config, **kwargs)
    else:
        raise ConfigError(f"Module type {module_config.type} not defined.")


def setup_css():
    setup_config_css()
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    css = """
.module-button {padding: 0; border: none;}
"""
    provider.load_from_data(css.encode())


def setup_config_css():
    if "XDG_CONFIG_HOME" in os.environ:
        config_path = os.path.expandvars("$XDG_CONFIG_HOME/ustatus/ustatus.css")
    else:
        config_path = os.path.expandvars("$HOME/.config/ustatus/ustatus.css")
    if os.path.exists(config_path):
        logging.info(f"Loading CSS from {config_path}")
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        provider.load_from_path(config_path)


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
