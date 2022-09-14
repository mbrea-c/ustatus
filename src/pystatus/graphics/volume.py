from gi.repository import Gtk


class Volume(Gtk.DrawingArea):
    def __init__(self, volume: float = 0) -> None:
        super().__init__()
        self.volume = volume
        self.connect("draw", lambda area, context: self.draw_battery(area, context))

    def update(self, volume: float):
        self.volume = volume
        self.queue_draw()

    def draw_battery(self, area, context):
        context.scale(area.get_allocated_width(), area.get_allocated_height())
        fg_color = area.get_style_context().get_color(Gtk.StateFlags.NORMAL)

        def draw_polygon(context, pts):
            x0, y0 = pts[0]
            context.move_to(x0, y0)
            for x, y in pts[1:]:
                context.line_to(x, y)
            context.close_path()

        volume = min([self.volume, 1])

        lw = 0.1
        margin = lw / 2

        outer_triangle = [
            (margin, 1 - margin),
            (1 - margin, margin),
            (1 - margin, 1 - margin),
        ]

        inner_triangle = [(0, 1), (volume, 1 - volume), (volume, 1)]

        context.set_line_width(0.1)
        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
        )
        draw_polygon(context, outer_triangle)
        context.stroke()
        draw_polygon(context, inner_triangle)
        context.fill()

        if self.volume > 1:
            v = self.volume % 1
            extra_triangle = [(0, 1), (v, 1 - v), (v, 1)]

            context.set_source_rgba(0.8, 0, 0, 1)
            draw_polygon(context, extra_triangle)
            context.fill()
