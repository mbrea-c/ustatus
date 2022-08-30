import argparse
import logging
from typing import Dict, List, Optional
from jsonschema import validate
import tomli
import os.path
import os
import copy
from pystatus.schema import schema, bar, get_python_type, module


class Config:
    def __init__(self):
        self._parse_arguments()
        paths = ["examples/pystatus.toml", get_user_config_path()]
        while paths:
            new_config = read_config_from_path(paths.pop())
            if new_config:
                self.config_dict = merge_configs(new_config, self.config_dict)
        validate(instance=self.config_dict, schema=schema)
        self.bar_configs = dict()
        self.module_configs = dict()
        for name, bar_dict in self.config_dict["bars"].items():
            self.bar_configs[name] = BarConfig(
                name=name,
                config_dict=self._inherit_close(
                    curr_dict=bar_dict, toml_dict=self.config_dict["bars"]
                ),
            )
        for name, module_dict in self.config_dict["modules"].items():
            self.module_configs[name] = ModuleConfig(
                name=name,
                config_dict=self._inherit_close(
                    curr_dict=module_dict, toml_dict=self.config_dict["modules"]
                ),
            )

    def _inherit_close(self, curr_dict, toml_dict):
        while "inherit" in curr_dict:
            inherited = copy.deepcopy(toml_dict[curr_dict["inherit"]])
            curr_dict.pop("inherit")
            curr_dict = merge_configs(source=curr_dict, destination=inherited)
        return curr_dict

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Start a pystatus instance of the bar of given name."
        )
        parser.add_argument(
            "bar_name",
            metavar="<bar>",
            type=str,
            help="name of the bar to spawn",
        )
        for prop_name, prop_details in bar["properties"].items():
            parser.add_argument(
                f"--{prop_name}",
                metavar=f"<{prop_name}>",
                type=get_python_type(prop_details),
                default=None,
                help=f"({prop_details['type']}) {prop_details.get('description', '')}",
            )
        args = parser.parse_args()
        self.bar_name = args.bar_name
        self.config_dict = dict(
            {"bars": dict({self.bar_name: dict()}), "modules": dict()}
        )
        for prop_name in bar["properties"]:
            arg = args.__getattribute__(prop_name)
            if arg is not None:
                self.config_dict["bars"][self.bar_name][prop_name] = arg

    def get_bar_config(self, bar_name):
        return self.bar_configs[bar_name]

    def get_module_config(self, module_name):
        return self.module_configs[module_name]


class ModuleConfig:
    def __init__(self, name: str, config_dict: Dict):
        self.name: str = name

        # Required settings
        self.type: str = config_dict["type"]

        # Optional settings
        self.show_label: bool = config_dict.get("show_label", False)
        self.label: Optional[str] = config_dict.get("label", None)
        self.length: int = config_dict.get("length", 25)

        # Semantic checks
        assert not self.show_label or self.label


class BarConfig:
    def __init__(self, name: str, config_dict: Dict):
        self.name: str = name

        # Required settings
        self.anchors: List[str] = config_dict["anchors"]
        self.orientation: str = config_dict["orientation"]

        # Optional settings
        self.modules_start: List[str] = config_dict.get("modules_start", [])
        self.modules_center: List[str] = config_dict.get("modules_center", [])
        self.modules_end: List[str] = config_dict.get("modules_end", [])
        self.exclusive: bool = config_dict.get("exclusive", False)
        self.width: int = config_dict.get("width", 25)
        self.separators: bool = config_dict.get("separators", False)


class ConfigError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"ConfigError: {self.message}"


def merge_configs(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge_configs(value, node)
        else:
            destination[key] = value

    return destination


def read_config_from_path(path: str):
    if os.path.exists(path):
        try:
            file = open(path, "rb")
        except:
            logging.error(f"Failed to open file {path}")
            return None
        try:
            toml_dict = tomli.load(file)
        except:
            logging.error(f"Failed to parse TOML file {path}. Exiting...")
            exit(1)
        file.close()
        logging.info(f"Loaded config file {path}")
        return toml_dict
    else:
        return None


def get_user_config_path():
    if "XDG_CONFIG_HOME" in os.environ:
        return os.path.expandvars("$XDG_CONFIG_HOME/pystatus/pystatus.toml")
    else:
        return os.path.expandvars("$HOME/.config/pystatus/pystatus.toml")
