from typing import Callable, Optional
from gi.repository import Gtk, GLib


class Module(Gtk.Frame):
    def __init__(
        self,
        gtk_orientation: Gtk.Orientation,
        toggle_modal: Callable,
        module_widget: Optional[Gtk.Widget] = None,
    ) -> None:
        super().__init__()
        if module_widget:
            self.set_module_widget(module_widget)
        self.gtk_orientation = gtk_orientation
        self.toggle_modal = toggle_modal

    def _update(self):
        raise NotImplementedError()

    def set_module_widget(self, module_widget):
        self.module_widget = module_widget
        self.add(self.module_widget)

    def get_popover_menubutton(self, modal_widget: Gtk.Widget):
        self.modal_widget = modal_widget
        button = Gtk.Button()
        button.connect("clicked", lambda _: self.toggle_modal(self.modal_widget))
        modal_widget.show_all()

        return button

    @staticmethod
    def __remove_button_frame__(button):
        button_style_context = button.get_style_context()
        button_style_context.add_class("module-button")


class ModuleWithModal(Module):
    def __init__(
        self,
        module_widget,
        modal_widget,
        gtk_orientation: Gtk.Orientation,
        toggle_modal: Callable,
    ) -> None:
        super().__init__(
            gtk_orientation=gtk_orientation,
            toggle_modal=toggle_modal,
        )
        button = self.get_popover_menubutton(modal_widget)
        Module.__remove_button_frame__(button)
        button.add(module_widget)
        self.set_module_widget(button)
        self.module_widget = module_widget

    def _update_modal(self):
        raise NotImplementedError()
