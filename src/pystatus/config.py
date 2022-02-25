import logging
from typing import Dict, List, Optional
import tomli
import os.path
import os
import copy


class Config:
    def __init__(self):
        paths = ["example/pystatus.toml", get_user_config_path()]
        toml_dict = None
        while paths:
            new_config = read_config_from_path(paths.pop())
            if new_config:
                if not toml_dict:
                    toml_dict = new_config
                else:
                    toml_dict = merge_configs(new_config, toml_dict)
        if not toml_dict:
            logging.error("Could not find any valid config file. Exiting...")
            exit(1)
        self.bar_configs = dict()
        self.module_configs = dict()
        for name, bar_dict in toml_dict["bars"].items():
            self.bar_configs[name] = BarConfig(
                name=name,
                config_dict=self._inherit_close(
                    curr_dict=bar_dict, toml_dict=toml_dict["bars"]
                ),
            )
        for name, module_dict in toml_dict["modules"].items():
            self.module_configs[name] = ModuleConfig(
                name=name,
                config_dict=self._inherit_close(
                    curr_dict=module_dict, toml_dict=toml_dict["modules"]
                ),
            )

    def _inherit_close(self, curr_dict, toml_dict):
        while "inherit" in curr_dict:
            inherited = copy.deepcopy(toml_dict[curr_dict["inherit"]])
            curr_dict.pop("inherit")
            curr_dict = merge_configs(source=curr_dict, destination=inherited)
        return curr_dict

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
