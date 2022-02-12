from typing import Optional
from gi.repository import Gtk, Gdk


class BarGraph(Gtk.DrawingArea):
    def __init__(self, n_values=4, color: Optional[Gdk.RGBA] = None) -> None:
        super().__init__()
        self.n_values = n_values
        self.values = [0] * n_values
        self.color = color
        self.connect("draw", lambda area, context: self.draw_bar_graph(area, context))

    def set_values(self, new_values):
        self.values = new_values
        self.queue_draw()

    def draw_bar_graph(self, area, context):
        context.scale(area.get_allocated_width(), area.get_allocated_height())
        if not self.color:
            fg_color = area.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        else:
            fg_color = self.color
        context.set_line_width(0.03)

        separation: float = 1 / (self.n_values)

        for i in range(self.n_values):
            x = i * separation
            height = self.values[i]

            context.rectangle(x, 1 - height, separation, height)
            context.set_source_rgba(
                fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
            )
            context.stroke_preserve()
            context.set_source_rgba(
                fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha / 2
            )
            context.fill()
