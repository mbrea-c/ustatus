from gi.repository import Gtk
from collections import deque


class LineGraph(Gtk.DrawingArea):
    def __init__(self, values=[], maxlen=10) -> None:
        super().__init__()

        seed = [0] * (maxlen - len(values)) + values

        self.values = deque(seed, maxlen=maxlen)
        self.connect("draw", lambda area, context: self.draw_line_graph(area, context))

    def push_values(self, new_values):
        self.values.extend(new_values)
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
