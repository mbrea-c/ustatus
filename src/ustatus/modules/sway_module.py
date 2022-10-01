import asyncio
import logging
from ustatus.config import ModuleConfig
from ustatus.module import Module
from typing import Callable, Dict, Iterable, Optional
from gi.repository import Gtk

from ustatus.utils.swaymsg import get_workspaces, subscribe, sway_command


class SwayModule(Module):
    def __init__(
        self,
        output: Optional[str],
        **kwargs,
    ):
        super().__init__(**kwargs)
        module_widget = SwayModuleWidget(
            gtk_orientation=self.gtk_orientation, on_select=self.on_select
        )
        self.set_module_widget(module_widget=module_widget)
        self.output = output
        asyncio.create_task(self._init_async())

    def on_select(self, num):
        asyncio.create_task(sway_command(f"workspace number {num}"))

    async def _init_async(self):
        workspaces = await self._get_workspaces()

        self.module_widget.setup_workspaces(workspaces)

        async for event in subscribe(["workspace"]):
            match event["change"]:
                case "focus":
                    if self._check_output(event["current"]):
                        self.module_widget.focus_workspace(event["current"])
                case "rename":
                    if self._check_output(event["current"]):
                        self.module_widget.rename_workspace(event["current"])
                case "init":
                    if self._check_output(event["current"]):
                        self.module_widget.init_workspace(event["current"])
                case "empty":
                    if self._check_output(event["current"]):
                        self.module_widget.remove_workspace(event["current"])
                case "move":
                    if self._check_output(event["current"]):
                        self.module_widget.move_workspace(event["current"])
                case "reload":
                    self.module_widget.setup_workspaces(await self._get_workspaces())

    def _check_output(self, workspace):
        return (not self.output) or workspace["output"] == self.output

    async def _get_workspaces(self) -> Iterable[Dict]:
        workspaces = await get_workspaces()
        if self.output:
            workspaces = filter(lambda w: w["output"] == self.output, workspaces)
        return workspaces


class WorkspaceLabel(Gtk.Label):
    def __init__(self, workspace):
        super().__init__(label=workspace["name"])
        self.workspace = workspace

    def get_num(self):
        return self.workspace["num"]

    def get_id(self):
        return self.workspace["id"]


class SwayModuleWidget(Gtk.FlowBox):
    def __init__(
        self,
        gtk_orientation: Gtk.Orientation,
        on_select: Callable,
        initial_workspaces: Optional[Iterable[Dict]] = None,
    ):
        match gtk_orientation:
            case Gtk.Orientation.HORIZONTAL:
                orientation = Gtk.Orientation.VERTICAL
            case Gtk.Orientation.VERTICAL:
                orientation = Gtk.Orientation.HORIZONTAL
            case other:
                raise Exception(f"Orientation {other} not recognized")
        super().__init__(orientation=orientation)
        self.on_select = on_select
        self.workspaces: Dict = dict()
        self.set_sort_func(
            lambda child1, child2, *user_data: -1
            if child1.get_child().get_num() < child2.get_child().get_num()
            else 1
        )
        self.set_homogeneous(True)
        self.connect("child-activated", self._on_child_activated)

        if initial_workspaces:
            self.setup_workspaces(initial_workspaces)

    def setup_workspaces(self, initial_workspaces):
        self._clear()
        for ws in initial_workspaces:
            self.init_workspace(ws)
            if ws["focused"]:
                self.focus_workspace(ws)
        self.show_all()

    def init_workspace(self, workspace):
        id = workspace["id"]
        if id in self.workspaces:
            raise Exception(
                f"Workspace {workspace['id']}:{workspace['num']}:{workspace['name']} already exists"
            )
        label = WorkspaceLabel(workspace=workspace)
        label.show()
        self.workspaces[id] = label
        self.add(label)

    def move_workspace(self, workspace):
        """Workspace is moved into current output"""
        id = workspace["id"]
        if id not in self.workspaces:
            label = WorkspaceLabel(workspace=workspace)
            label.show()
            self.workspaces[id] = label
            self.add(label)

    def remove_workspace(self, workspace):
        if workspace["id"] not in self.workspaces:
            raise Exception(
                f"Workspace {workspace['id']}:{workspace['num']}:{workspace['name']} does not exist, can't be removed!"
            )
        label = self.workspaces.pop(workspace["id"])
        self.remove(label)

    def rename_workspace(self, workspace):
        id = workspace["id"]
        if id not in self.workspaces:
            raise Exception(
                f"Workspace {workspace['id']}:{workspace['num']}:{workspace['name']} does not exist, can't be renamed!"
            )
        self.workspaces[id].set_label(workspace["name"])

    def focus_workspace(self, workspace):
        id = workspace["id"]
        if id not in self.workspaces:
            raise Exception(
                f"Workspace {workspace['id']}:{workspace['num']}:{workspace['name']} does not exist, can't be focused!"
            )
        self.select_child(self._find_child_with_label(self.workspaces[id]))

    def _find_child_with_label(self, label):
        for child in self.get_children():
            if child.get_child() == label:
                return child
        raise Exception("Child not found")

    def _clear(self):
        while True:
            try:
                _, label = self.workspaces.popitem()
                self.remove(label)
            except KeyError:
                break

    def _on_child_activated(self, flow_box, child):
        self.on_select(child.get_child().get_num())
