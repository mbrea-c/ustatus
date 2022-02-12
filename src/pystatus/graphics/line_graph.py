from typing import Optional
from gi.repository import Gtk, Gdk
from collections import deque


class LineGraph(Gtk.DrawingArea):
    def __init__(
        self,
        n_values=100,
        color: Optional[Gdk.RGBA] = None,
        min: float = 0,
        max: float = 1,
    ) -> None:
        super().__init__()
        self.min = min
        self.max = max
        self._update_range()
        self.n_values = n_values
        self.values = deque([0] * n_values, maxlen=n_values)
        self.color = color
        self.connect("draw", lambda area, context: self.draw_line_graph(area, context))

    def set_max(self, max):
        self.max = max
        self._update_range()

    def set_min(self, min):
        self.min = min
        self._update_range()

    def _update_range(self):
        self.range = self.max - self.min

    def set_values(self, new_values):
        self.values = deque(new_values, maxlen=self.n_values)
        self.queue_draw()

    def push_value(self, new_value):
        self.values.append(new_value)
        self.queue_draw()

    def draw_line_graph(self, area, context):
        context.scale(area.get_allocated_width(), area.get_allocated_height())
        if not self.color:
            fg_color = area.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        else:
            fg_color = self.color
        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
        )

        maxsize = max([area.get_allocated_width(), area.get_allocated_height()])
        context.set_line_width(1 / maxsize)

        separation: float = 1 / (len(self.values) - 1)

        for i, val in enumerate(self.values):
            x = i * separation
            height = (val - self.min) / self.range

            context.line_to(x, 1 - height)

        context.stroke_preserve()

        context.line_to(1, 1)
        context.line_to(0, 1)

        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha / 2
        )
        context.fill()
