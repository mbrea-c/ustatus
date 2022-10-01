from typing import Callable
from gi.repository import Gtk, GLib
import pulsectl_asyncio, asyncio
from ustatus.config import ModuleConfig
from ustatus.graphics.meter import Meter
from ustatus.graphics.volume import Volume
from ustatus.module import Module
from ustatus.utils.swaymsg import get_workspaces


class VolumeModule(Module):
    def __init__(self, gtk_orientation: Gtk.Orientation, **kwargs) -> None:
        super().__init__(gtk_orientation=gtk_orientation, **kwargs)
        module_widget = VolumeModuleWidget(gtk_orientation=gtk_orientation)
        self.set_module_widget(module_widget)

        self.sinks = dict()
        self.pulse = pulsectl_asyncio.PulseAsync("ustatus")

        self.updater_task = asyncio.create_task(self._init_async())
        self.update_lock = False

    def _update_sinks(self, name_volume_dict: dict):
        # New additions and updates
        for name, volume in name_volume_dict.items():
            if name in self.sinks.keys():
                label = self.sinks[name]
                label.update(volume)
            else:
                label = SinkVolume(
                    name,
                    volume,
                    gtk_orientation=Gtk.Orientation.HORIZONTAL,
                )
                self.module_widget.add_sink_volume(label)
                self.sinks[name] = label
        # Removals
        pending_removal = []
        for name, label in self.sinks.items():
            if name not in name_volume_dict.keys():
                pending_removal.append((name, label))
        for name, label in pending_removal:
            self.module_widget.remove_sink_volume(label)
            self.sinks.pop(name)

    async def _init_async(self):
        await self.pulse.connect()
        await self._update()
        async for _ in self.pulse.subscribe_events("all"):
            await self._update()

    async def _update(self) -> None:
        if not self.update_lock:
            self.update_lock = True
            sinks = await self.pulse.sink_list()
            name_volume_dict = {
                s.name: await self.pulse.volume_get_all_chans(s) for s in sinks
            }
            self._update_sinks(name_volume_dict)
            self.queue_draw()
            self.update_lock = False


class SinkVolume(Gtk.Box):
    def __init__(
        self,
        name: str,
        volume: float,
        gtk_orientation: Gtk.Orientation,
    ) -> None:
        super().__init__()
        container = Gtk.Box(orientation=gtk_orientation, spacing=5)
        self.label = Gtk.Label(label=self._label(volume))
        self.meter = Meter(volume)
        self.meter.set_size_request(40, 1)
        self.meter.set_hexpand(True)
        self.meter.set_vexpand(False)
        self.set_tooltip_text(name)
        container.pack_start(self.meter, expand=False, fill=False, padding=0)
        container.add(self.label)
        self.set_center_widget(container)
        self.show_all()

    def update(self, volume: float) -> None:
        self.label.set_label(self._label(volume))
        self.meter.update(volume)

    def _label(self, volume: float) -> str:
        return f"{volume * 100:.0f}%"


class VolumeModuleWidget(Gtk.Box):
    def __init__(self, gtk_orientation: Gtk.Orientation):
        super().__init__(orientation=gtk_orientation, spacing=5)

    def add_sink_volume(self, sink_volume: SinkVolume):
        self.pack_start(sink_volume, expand=True, fill=True, padding=0)

    def remove_sink_volume(self, sink_volume: SinkVolume):
        self.remove(sink_volume)
