from typing import Callable
from gi.repository import Gtk, GLib
from pystatus.graphics.line_graph import LineGraph
from pystatus.graphics.bar_graph import BarGraph
from pystatus.module import ModuleWithModal
import psutil
from pystatus.cpuinfo import get_core_per_cpu
from collections import deque
import itertools


class CpuModule(ModuleWithModal):
    def __init__(
        self,
        gtk_orientation: Gtk.Orientation,
        uptate_period_seconds=3,
        history_length=20,
    ) -> None:
        module_widget = CpuModuleWidget()
        modal_widget = CpuModuleModalWidget(history_length=history_length)
        self.history_length = history_length
        self.cpu_history = History(
            updater=self.update_cpu_history, maxlen=history_length
        )
        self.temp_history = History(
            updater=self.update_temp_history, maxlen=history_length
        )
        super().__init__(module_widget, modal_widget, gtk_orientation=gtk_orientation)
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self._update())
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self._update_modal())

    def _update(self):
        self.cpu_history.update()
        self.temp_history.update()
        self.module_widget.update(self.cpu_history.peek_one())
        return True

    def _update_modal(self):
        self.modal_widget.update(
            self.cpu_history.peek_n(self.history_length),
            self.temp_history.peek_n(self.history_length),
        )
        return True

    def update_cpu_history(self):
        cpu_percents = [x / 100 for x in psutil.cpu_percent(interval=None, percpu=True)]
        return cpu_percents

    def update_temp_history(self):
        coretemp = psutil.sensors_temperatures()["coretemp"]
        temps = []
        for ct in coretemp:
            if ct.critical:
                temps.append(ct.current / ct.critical)
            else:
                temps.append(ct.current / 100)
        return temps


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
        core_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        temp_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        coretemp = psutil.sensors_temperatures()["coretemp"]
        self.temps = []
        for ct in coretemp:
            temp = Temp(label=ct.label)
            self.temps.append(temp)
            temp_container.add(temp)
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
        self.add(temp_container)

    def update(self, cpu_values, temp_values):
        for v, cpu in zip(cpu_values, self.cpus):
            cpu.update(v)
        for v, temp in zip(temp_values, self.temps):
            temp.update(v)


class History:
    def __init__(
        self,
        updater: Callable,
        maxlen: int = 100,
    ):
        self.maxlen = maxlen
        seed = [0] * maxlen
        self.history = [deque(seed, maxlen=maxlen) for _ in range(psutil.cpu_count())]
        self.updater = updater

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
        new_value = self.updater()
        self.push_value(new_value)


class Cpu(Gtk.Box):
    def __init__(self, cpu_id: int, history_length: int = 20) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(cpu_id))
        self.curr_label = Gtk.Label(label="")
        self.meter = LineGraph(n_values=history_length)
        self.meter.set_size_request(100, 100)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)

    def update(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)
        self.curr_label.set_label(f"{new_values[-1]*100:.1f}%")

    def __label__(self, cpu_id: int) -> str:
        return f"CPU {cpu_id}"


class Temp(Gtk.Box):
    def __init__(self, label: str, history_length: int = 20) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=label)
        self.curr_label = Gtk.Label(label="")
        self.meter = LineGraph(n_values=history_length)
        self.meter.set_size_request(100, 100)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)

    def update(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)
        self.curr_label.set_label(f"{new_values[-1] * 100:.1f}°C")


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
