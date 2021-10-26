from gi.repository import Gtk, GLib
from line_graph import LineGraph
import psutil


class CpuModule(Gtk.Frame):
    def __init__(self, uptate_period_seconds=3) -> None:
        super().__init__()
        top_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label="CPU Usage")
        graph_container = Gtk.FlowBox()
        self.cpu_graphs = [LineGraph() for _ in range(psutil.cpu_count())]
        for i, graph in enumerate(self.cpu_graphs):
            graph_label = Gtk.Label(label=f"CPU {i}")
            cont = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            cont.add(graph_label)
            cont.add(graph)
            graph.set_size_request(50, 50)
            graph_container.add(cont)

        top_container.add(label)
        top_container.add(graph_container)
        self.add(top_container)
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self.update())

    def update(self):
        cpu_percents = [x / 100 for x in psutil.cpu_percent(interval=None, percpu=True)]
        for i, val in enumerate(cpu_percents):
            self.cpu_graphs[i].push_values([val])
        return True
