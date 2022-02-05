import logging
from typing import Dict
import tomli
import os.path
import os
from pystatus.modules.battery_module import BatteryModule
from pystatus.modules.cpu_module import CpuModule
from pystatus.modules.mpris_module import MprisModule
from pystatus.modules.tray_module import TrayModule
from pystatus.modules.volume_module import VolumeModule


def read_config():
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
    return toml_dict


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


def instantiate_modules_for_bar(bar_name: str, config: Dict):
    bar = config["bars"][bar_name]
    module_names = bar["modules"]

    module_configs = config["modules"]

    modules = []
    for module_name in module_names:
        module_config = module_configs[module_name]
        match module_config["type"]:
            case "volume":
                modules.append(VolumeModule())
            case "battery":
                modules.append(BatteryModule())
            case "mpris":
                modules.append(MprisModule())
            case "cpu":
                modules.append(CpuModule())
            case "tray":
                modules.append(TrayModule())
    return modules


def get_user_config_path():
    if "XDG_CONFIG_HOME" in os.environ:
        return os.path.expandvars("$XDG_CONFIG_HOME/pystatus/pystatus.toml")
    else:
        return os.path.expandvars("$HOME/.config/pystatus/pystatus.toml")
