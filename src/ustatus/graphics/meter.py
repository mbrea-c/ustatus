from gi.repository import Gtk


class Meter(Gtk.DrawingArea):
    def __init__(self, value: float = 0) -> None:
        super().__init__()
        self.value = value
        self.connect("draw", lambda area, context: self.draw(area, context))

    def update(self, volume: float):
        self.value = volume
        self.queue_draw()

    def draw(self, area, context):
        width = area.get_allocated_width()
        height = area.get_allocated_height()

        lw_constant = 2
        lw_horizontal = lw_constant
        lw_vertical = lw_constant
        fg_color = area.get_style_context().get_color(Gtk.StateFlags.NORMAL)

        def draw_polygon(context, pts):
            x0, y0 = pts[0]
            context.move_to(x0, y0)
            for x, y in pts[1:]:
                context.line_to(x, y)
            context.close_path()

        context.set_source_rgba(
            fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
        )
        context.set_line_width(lw_horizontal)
        context.move_to(0, 0)
        context.line_to(area.get_allocated_width(), 0)
        context.stroke()

        context.move_to(0, area.get_allocated_height())
        context.line_to(area.get_allocated_width(), area.get_allocated_height())
        context.stroke()

        context.set_line_width(lw_vertical)
        context.move_to(0, 0)
        context.line_to(0, area.get_allocated_height())
        context.stroke()

        context.set_line_width(lw_vertical)
        context.move_to(area.get_allocated_width(), 0)
        context.line_to(area.get_allocated_width(), area.get_allocated_height())
        context.stroke()

        measure = [
            (0, 0),
            (0, height),
            (min(self.value, 1) * width, height),
            (min(self.value, 1) * width, 0),
        ]
        draw_polygon(context, measure)
        context.fill()

        if self.value > 1:
            extra_measure = [
                (0, 0),
                (0, height),
                (min(self.value-1, 1) * width, height),
                (min(self.value-1, 1) * width, 0),
            ]

            context.set_source_rgba(0.8, 0, 0, 1)
            draw_polygon(context, extra_measure)
            context.fill()
