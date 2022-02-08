import logging
from typing import Dict
import tomli
import os.path
import os


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
        self.config = toml_dict

    def get_entry_for_bar(self, bar_name, key):
        return self.config["bars"][bar_name][key]

    def get_entry_for_module(self, module_name, key):
        return self.config["modules"][module_name][key]


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
