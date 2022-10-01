from typing import Callable
from gi.repository import Gtk, Gdk, GLib
from ustatus.config import ModuleConfig
from ustatus.graphics.line_graph import LineGraph
from ustatus.graphics.bar_graph import BarGraph
from ustatus.module import Module
import psutil
from ustatus.cpuinfo import get_core_per_cpu
from collections import deque
import itertools


class CpuModule(Module):
    def __init__(
        self, bar_width: int, uptate_period_seconds=1, history_length=60, **kwargs
    ) -> None:
        module_widget = CpuModuleWidget(bar_width=bar_width)
        modal_widget = CpuModuleModalWidget(history_length=history_length)
        self.history_length = history_length
        self.cpu_history = History(
            updater=self.update_cpu_history, maxlen=history_length
        )
        self.freq_history = History(
            updater=self.update_freq_history, maxlen=history_length
        )
        self.temp_history = History(
            updater=self.update_temp_history, maxlen=history_length
        )
        # self.fans_history = History(
        # updater=self.update_fans_history, maxlen=history_length
        # )
        super().__init__(
            module_widget=module_widget,
            bar_width=bar_width,
            **kwargs,
        )
        modal_button = self.get_popover_menubutton(modal_widget=modal_widget)
        self.module_widget.set_popover_menubutton(modal_button)
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self._update())
        GLib.timeout_add(uptate_period_seconds * 1000, lambda: self._update_modal())

    def _update(self):
        self.cpu_history.update()
        self.freq_history.update()
        self.temp_history.update()
        # self.fans_history.update()
        self.module_widget.update(self.cpu_history.peek_one())
        return True

    def _update_modal(self):
        self.modal_widget.push_value(
            self.cpu_history.peek_one(),
            self.temp_history.peek_one(),
        )
        # self.modal_widget.push_fans_value(self.fans_history.peek_one(), "thinkpad")
        self.modal_widget.push_freq_value(self.freq_history.peek_one())
        return True

    def update_cpu_history(self):
        cpu_percents = [x / 100 for x in psutil.cpu_percent(interval=None, percpu=True)]
        return cpu_percents

    def update_freq_history(self):
        freqs = [x.current for x in psutil.cpu_freq(percpu=True)]
        return freqs

    def update_fans_history(self):
        thinkpad = psutil.sensors_fans()["thinkpad"]
        fans = []
        for fan in thinkpad:
            fans.append(fan.current)
        return fans

    def update_temp_history(self):
        coretemp = psutil.sensors_temperatures()["coretemp"]
        temps = []
        for ct in coretemp:
            temps.append(ct.current)
        return temps


class CpuModuleWidget(Gtk.Box):
    def __init__(self, bar_width: int) -> None:
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.button = None
        self.meter = BarGraph(
            n_values=psutil.cpu_count(),
            color=Gdk.RGBA(red=0.31, green=0.31, blue=0.80, alpha=1),
        )
        self.meter.set_size_request(bar_width, bar_width)
        self.add(self.meter)

    def update(self, values):
        self.meter.set_values(values)

    def set_popover_menubutton(self, button: Gtk.Widget):
        if self.button:
            self.remove(self.button)
        self.button = button
        button_image = Gtk.Image.new_from_icon_name(
            "go-down-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.button.set_image(button_image)
        Module.__remove_button_frame__(self.button)
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.add(button)


class CpuModuleModalWidget(Gtk.Box):
    def __init__(self, history_length: int = 20) -> None:
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.history_length = history_length
        label = Gtk.Label(label="CPU Usage")
        self.add(label)
        self.init_cpu_usage()
        self.init_cpu_freq()
        self.init_coretemp()
        # self.init_fanspeed()

    def init_coretemp(self):
        temp_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        coretemp = psutil.sensors_temperatures()["coretemp"]
        self.temps = []
        for ct in coretemp:
            if ct.critical:
                crit = ct.critical
            else:
                crit = 100
            temp = Temp(label=ct.label, history_length=self.history_length, crit=crit)
            self.temps.append(temp)
            temp_container.add(temp)
        self.add(temp_container)

    def init_cpu_usage(self):
        core_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cpu_info = get_core_per_cpu()
        core_ids = list(set(cpu_info))
        cores = [Core(id) for id in core_ids]
        for core in cores:
            core_container.add(core)
        self.cpus = [
            Cpu(i, history_length=self.history_length)
            for i in range(psutil.cpu_count())
        ]
        for i, cpu in enumerate(self.cpus):
            cores[cpu_info[i]].add_cpu(cpu)
        self.add(core_container)

    def init_cpu_freq(self):
        core_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cpu_info = get_core_per_cpu()
        core_ids = list(set(cpu_info))
        cores = [Core(id) for id in core_ids]
        for core in cores:
            core_container.add(core)
        self.freqs = [
            Freq(i, history_length=self.history_length, max_freq=freq.max)
            for i, freq in enumerate(psutil.cpu_freq(percpu=True))
        ]
        for i, cpu in enumerate(self.freqs):
            cores[cpu_info[i]].add_cpu(cpu)
        self.add(core_container)

    def init_fanspeed(self):
        self.fans = dict()
        fanspeed_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        fan_dict = psutil.sensors_fans()
        for key, val in fan_dict.items():
            self.fans[key] = []
            for i, fan in enumerate(val):
                if fan.label:
                    label = fan.label
                else:
                    label = f"{key} {i}"
                fan_gtk = FanSpeed(label=label, history_length=self.history_length)
                self.fans[key].append(fan_gtk)
                fanspeed_container.add(fan_gtk)

        self.add(child=fanspeed_container)

    def set_values(self, cpu_values, temp_values):
        for v, cpu in zip(cpu_values, self.cpus):
            cpu.set_values(v)
        for v, temp in zip(temp_values, self.temps):
            temp.set_values(v)

    def set_freq_values(self, freq_values):
        for v, freq in zip(freq_values, self.freqs):
            freq.set_values(v)

    def push_freq_value(self, freq_values):
        for v, freq in zip(freq_values, self.freqs):
            freq.push_value(v)

    def set_fans_values(self, fan_values, fan_key):
        for v, fan in zip(fan_values, self.fans[fan_key]):
            fan.set_values(v)

    def push_fans_value(self, fan_values, fan_key):
        for v, fan in zip(fan_values, self.fans[fan_key]):
            fan.push_value(v)

    def push_value(self, cpu_value, temp_value):
        for v, cpu in zip(cpu_value, self.cpus):
            cpu.push_value(v)
        for v, temp in zip(temp_value, self.temps):
            temp.push_value(v)


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
        self.meter = LineGraph(
            n_values=history_length,
            color=Gdk.RGBA(red=0.31, green=0.31, blue=0.80, alpha=1),
        )
        self.meter.set_size_request(100, 100)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)

    def set_values(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)
        self.curr_label.set_label(f"{new_values[-1]*100:.1f}%")

    def push_value(self, new_value: float) -> None:
        self.meter.push_value(new_value)
        self.curr_label.set_label(f"{new_value * 100:.1f}%")

    def __label__(self, cpu_id: int) -> str:
        return f"CPU {cpu_id}"


class Freq(Gtk.Box):
    def __init__(self, cpu_id: int, history_length: int = 20, max_freq=3000) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(cpu_id))
        self.curr_label = Gtk.Label(label="")
        self.meter = LineGraph(
            n_values=history_length,
            color=Gdk.RGBA(red=0.21, green=0.60, blue=0.60, alpha=1),
        )
        self.meter.set_size_request(100, 100)
        self.set_max_freq(max_freq)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)

    def set_max_freq(self, max_freq):
        self.max_freq = max_freq
        self.meter.set_max(self.max_freq)

    def set_values(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)
        self.curr_label.set_label(f"{new_values[-1]:.1f} MHz")

    def push_value(self, new_value: float) -> None:
        self.meter.push_value(new_value)
        self.curr_label.set_label(f"{new_value:.1f} MHz")

    def __label__(self, cpu_id: int) -> str:
        return f"CPU {cpu_id}"


class Temp(Gtk.Box):
    def __init__(self, label: str, history_length: int = 20, crit: float = 100) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=label)
        self.curr_label = Gtk.Label(label="")
        self.crit = crit
        self.meter = LineGraph(
            n_values=history_length,
            color=Gdk.RGBA(red=0.80, green=0.31, blue=0.31, alpha=1),
        )
        self.meter.set_size_request(100, 100)
        self.meter.set_max(crit)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)

    def set_values(self, new_values: list[float]) -> None:
        self.meter.set_values(new_values)
        self.curr_label.set_label(f"{new_values[-1]:.1f}°C")

    def push_value(self, new_value: float) -> None:
        self.meter.push_value(new_value)
        self.curr_label.set_label(f"{new_value:.1f}°C")


class FanSpeed(Gtk.Box):
    def __init__(self, label: str, history_length: int = 20) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.history_length = history_length
        self.label = Gtk.Label(label=label)
        self.label.connect(
            "size-allocate",
            lambda label, size: label.set_size_request(size.width - 1, -1),
        )
        self.curr_label = Gtk.Label(label="")
        self.meter = LineGraph(
            n_values=history_length,
            color=Gdk.RGBA(red=0.31, green=0.80, blue=0.31, alpha=1),
        )
        self.meter.set_size_request(100, 100)
        self.add(self.meter)
        self.add(self.curr_label)
        self.add(self.label)
        self.running_max = 1
        self.running_max_age = 0

    def set_values(self, new_values: list[float]) -> None:
        assert len(new_values) == self.history_length
        self.running_max = max(new_values)
        self.running_max_age = 0
        self.meter.set_values(new_values)
        self.meter.set_max(self.running_max)
        self.curr_label.set_label(f"{new_values[-1]:d} RPM")

    def push_value(self, new_value: float) -> None:
        self.meter.push_value(new_value)
        self.curr_label.set_label(f"{new_value:d} RPM")

        self.running_max_age += 1
        if new_value > self.running_max:
            self.running_max = new_value
            self.running_max_age = 0
            self.meter.set_max(self.running_max)
        elif self.running_max_age > self.history_length:
            self.running_max = max(self.meter.values)
            self.running_max_age = 0
            self.meter.set_max(self.running_max)


class Core(Gtk.Box):
    def __init__(self, core_id: int) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.core_id = core_id
        self.cpu_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(core_id))
        self.add(self.cpu_container)
        self.add(self.label)

    def add_cpu(self, cpu_widget: Gtk.Widget) -> None:
        self.cpu_container.add(cpu_widget)

    def __label__(self, core_id: int) -> str:
        return f"Core {core_id}"
