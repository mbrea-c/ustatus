from gi.repository import Gtk, GLib
from pystatus.graphics.line_graph import LineGraph
from pystatus.graphics.bar_graph import BarGraph
from pystatus.module import ModuleWithModal
import psutil
from pystatus.cpuinfo import get_core_per_cpu
from collections import deque
import itertools


class CpuModule(ModuleWithModal):
    def __init__(self, uptate_period_seconds=3, history_length=20) -> None:
        module_widget = CpuModuleWidget()
        modal_widget = CpuModuleModalWidget(history_length=history_length)
        self.history_length = history_length
        self.history = CpuHistory(maxlen=history_length)
        super().__init__(module_widget, modal_widget)
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self.__update__())
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self.__update_modal__())

    def __update__(self):
        self.history.update()
        self.module_widget.update(self.history.peek_one())
        return True

    def __update_modal__(self):
        self.modal_widget.update(self.history.peek_n(self.history_length))
        return True


class CpuModuleWidget(Gtk.Box):
    def __init__(self) -> None:
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.meter = BarGraph(n_values=psutil.cpu_count())
        self.meter.set_size_request(25, 25)
        label = Gtk.Label(label="CPU")
        self.add(label)
        self.add(self.meter)

    def update(self, values):
        self.meter.set_values(values)


class CpuModuleModalWidget(Gtk.Box):
    def __init__(self, history_length: int = 20) -> None:
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label="CPU Usage")
        core_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        cpu_info = get_core_per_cpu()
        core_ids = list(set(cpu_info))
        cores = [Core(id) for id in core_ids]
        for core in cores:
            core_container.add(core)
        self.cpus = [
            Cpu(i, history_length=history_length) for i in range(psutil.cpu_count())
        ]
        for i, cpu in enumerate(self.cpus):
            cores[cpu_info[i]].add_cpu(cpu)

        self.add(label)
        self.add(core_container)

    def update(self, values):
        for v, cpu in zip(values, self.cpus):
            cpu.update(v)


class CpuHistory:
    def __init__(self, maxlen=100):
        self.maxlen = maxlen
        seed = [0] * maxlen
        self.history = [deque(seed, maxlen=maxlen) for _ in range(psutil.cpu_count())]

    def push_value(self, new_value):
        for value, thread_history in zip(new_value, self.history):
            thread_history.popleft()
            thread_history.append(value)

    def peek_one(self):
        return [thread_history[-1] for thread_history in self.history]

    def peek_n(self, n):
        return [
            list(itertools.islice(thread_history, self.maxlen - n, self.maxlen))
            for thread_history in self.history
        ]

    def update(self):
        cpu_percents = [x / 100 for x in psutil.cpu_percent(interval=None, percpu=True)]
        self.push_value(cpu_percents)


class Cpu(Gtk.Box):
    def __init__(self, cpu_id: int, history_length: int = 20) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(cpu_id))
        self.meter = LineGraph(n_values=history_length)
        self.meter.set_size_request(50, 50)
        self.add(self.meter)
        self.add(self.label)

    def update(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)

    def __label__(self, cpu_id: int) -> str:
        return f"CPU {cpu_id}"


class Core(Gtk.Box):
    def __init__(self, core_id: int) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.core_id = core_id
        self.cpu_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(core_id))
        self.add(self.label)
        self.add(self.cpu_container)

    def add_cpu(self, cpu_widget: Gtk.Widget) -> None:
        self.cpu_container.add(cpu_widget)

    def __label__(self, core_id: int) -> str:
        return f"Core {core_id}"
