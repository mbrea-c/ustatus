from gi.repository import Gtk
from cairo import Operator, FillRule


class Battery(Gtk.DrawingArea):
    def __init__(self, charge: float = 0, ac: bool = False) -> None:
        super().__init__()
        self.charge = charge
        self.ac = ac
        self.connect("draw", lambda area, context: self.draw_battery(area, context))

    def update(self, charge: float, ac: bool):
        self.charge = charge
        self.ac = ac
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

        battery_line_width = 0.05
        battery_width = 0.4
        battery_height = 0.60
        cap_height = 0.1
        cap_width = 0.2
        battery_x = 0.5 - battery_width / 2
        battery_y = 0.5 - battery_height / 2 + cap_height / 2
        cap_x = 0.5 - cap_width / 2

        pts_outer = [
            (battery_x, battery_y),
            (cap_x, battery_y),
            (cap_x, battery_y - cap_height),
            (cap_x + cap_width, battery_y - cap_height),
            (cap_x + cap_width, battery_y),
            (battery_x + battery_width, battery_y),
            (battery_x + battery_width, battery_y + battery_height),
            (battery_x, battery_y + battery_height),
        ]

        battery_inner_x = battery_x + battery_line_width
        battery_inner_y = battery_y + battery_line_width
        battery_inner_width = battery_width - 2 * battery_line_width
        battery_inner_height = (battery_height - 2 * battery_line_width) * (
            1 - self.charge
        )

        pts_inner = [
            (battery_inner_x, battery_inner_y),
            (battery_inner_x + battery_inner_width, battery_inner_y),
            (
                battery_inner_x + battery_inner_width,
                battery_inner_y + battery_inner_height,
            ),
            (battery_inner_x, battery_inner_y + battery_inner_height),
        ]

        context.set_line_width(0.05)
        if self.charge > 0.15 or self.ac:
            context.set_source_rgba(
                fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
            )
        else:
            context.set_source_rgb(0.8, 0, 0)
        context.set_fill_rule(FillRule.EVEN_ODD)

        draw_polygon(context, pts_outer)
        context.clip()
        draw_polygon(context, pts_inner)
        context.new_sub_path()
        context.move_to(0,0)
        context.line_to(1,0)
        context.line_to(1,1)
        context.line_to(0,1)
        context.close_path()
        context.clip()
        context.paint()
        context.reset_clip()

        if self.ac:
            lightning_ratio = 0.5
            lightning_width = battery_width * lightning_ratio
            lightning_height = battery_height * lightning_ratio
            lightning_x = battery_x + (battery_width - lightning_width) / 2
            lightning_y = battery_y + (battery_height - lightning_height) / 2

            def adjust_point(p):
                x, y = p
                return (
                    lightning_width * x + lightning_x,
                    lightning_height * y + lightning_y,
                )

            pts = [
                adjust_point((0, 0.5)),
                adjust_point((0.75, 0)),
                adjust_point((0.625, 0.375)),
                adjust_point((1, 0.5)),
                adjust_point((0.25, 1)),
                adjust_point((0.375, 0.625))
            ]
            context.set_line_width(0.03)
            draw_polygon(context, pts)
            context.set_source_rgba(
                fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha
            )
            context.set_operator(Operator.SOURCE)
            context.fill_preserve()
            context.set_source_rgba(
                1-fg_color.red, 1-fg_color.green, 1-fg_color.blue, fg_color.alpha
            )
            context.stroke()
