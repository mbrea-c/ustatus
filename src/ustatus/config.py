import argparse
import logging
from typing import Dict
from jsonschema import validate
import tomli
import os.path
import os
import copy
from ustatus.schema import cmdline_friendly, schema, bar, get_python_type, module


class Config:
    def __init__(self):
        self.config_dict = dict({"bars": dict(), "modules": dict()})
        self._update_with_config_files()
        self._update_with_arguments()
        self._update_with_defaults()
        validate(instance=self.config_dict, schema=schema)

    def _inherit_close(self, curr_dict, toml_dict):
        while "inherit" in curr_dict:
            inherited = copy.deepcopy(toml_dict[curr_dict["inherit"]])
            curr_dict.pop("inherit")
            curr_dict = merge_configs(source=curr_dict, destination=inherited)
        return curr_dict

    def _update_with_config_files(self):
        paths = ["examples/ustatus.toml", get_user_config_path()]
        while paths:
            new_config = read_config_from_path(paths.pop())
            if new_config:
                self.config_dict = merge_configs(new_config, self.config_dict)

    def _update_with_arguments(self):
        parser = argparse.ArgumentParser(
            description="Start a ustatus instance of the bar of given name."
        )
        parser.add_argument(
            "bar_name",
            metavar="<bar>",
            type=str,
            help="name of the bar to spawn",
        )
        for prop_name, prop_details in bar["properties"].items():
            if cmdline_friendly(prop_details):
                parser.add_argument(
                    f"--{prop_name}",
                    metavar=f"<{prop_name}>",
                    type=get_python_type(prop_details),
                    default=None,
                    help=f"({prop_details['type']}) {prop_details.get('description', '')}",
                )
        args = parser.parse_args()
        self.bar_name = args.bar_name
        if self.bar_name not in self.config_dict["bars"]:
            self.config_dict["bars"][self.bar_name] = dict()
        for prop_name, prop_details in bar["properties"].items():
            if cmdline_friendly(prop_details):
                arg = args.__getattribute__(prop_name)
                if arg is not None:
                    self.config_dict["bars"][self.bar_name][prop_name] = arg

    def _update_with_defaults(self):
        for bar_config in self.config_dict["bars"].values():
            for prop_name, prop_details in bar["properties"].items():
                if prop_name not in bar_config:
                    bar_config[prop_name] = prop_details.get("default", None)

        for module_config in self.config_dict["modules"].values():
            for prop_name, prop_details in module["properties"].items():
                if prop_name not in module_config:
                    module_config[prop_name] = prop_details.get("default", None)

    def get_bar_config(self, bar_name):
        return BarConfig(bar_name, self.config_dict)

    def get_module_config(self, module_name):
        return ModuleConfig(module_name, self.config_dict)


class ModuleConfig:
    def __init__(self, module_name: str, config_dict: Dict):
        self.module_name = module_name
        self.config_dict = config_dict

    def __getattr__(self, name):
        return self.config_dict["modules"][self.module_name][name]


class BarConfig:
    def __init__(self, bar_name: str, config_dict: Dict):
        self.bar_name = bar_name
        self.config_dict = config_dict

    def __getattr__(self, name):
        return self.config_dict["bars"][self.bar_name][name]


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
        return os.path.expandvars("$XDG_CONFIG_HOME/ustatus/ustatus.toml")
    else:
        return os.path.expandvars("$HOME/.config/ustatus/ustatus.toml")
