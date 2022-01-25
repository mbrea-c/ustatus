from gi.repository import Gtk
from collections import deque


class LineGraph(Gtk.DrawingArea):
    def __init__(self, n_values=100) -> None:
        super().__init__()
        self.n_values = n_values
        self.values = [0] * n_values
        self.connect("draw", lambda area, context: self.draw_line_graph(area, context))

    def set_values(self, new_values):
        self.values = new_values
        self.queue_draw()

    def draw_line_graph(self, area, context):
        context.scale(area.get_allocated_width(), area.get_allocated_height())
        fg_color = area.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
        )
        context.set_line_width(0.03)

        separation: float = 1 / (len(self.values) - 1)

        for i in range(len(self.values)):
            x = i * separation
            height = self.values[i]

            context.line_to(x, 1 - height)

        context.stroke_preserve()

        context.line_to(1, 1)
        context.line_to(0, 1)

        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha / 2
        )
        context.fill()
