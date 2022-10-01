from functools import reduce
from typing import Dict, Iterable
from ustatus.schema import bar, cmdline_friendly, module


def generate_docs():
    docs = f"""
# Configuration guide
Configuration is written in [TOML](https://toml.io/en/). Ustatus will read a file called `ustatus.toml` at `$XDG_CONFIG_HOME/ustatus/ustatus.toml` or at `$HOME/.config/ustatus/ustatus.toml` if the former is not defined.

## Bar configuration
All *bar configurations* should be under a table called `bars`. For example, a bar called `mystatusbar` is configured as in the following snippet:
```toml
[bars.mystatusbar]
modules_center = [
  "cpu",
  "tray",
  "power",
]
anchors = ["right"]
orientation = "vertical"
separators = true
width = 90
```
As long as the included modules are also defined (see [module configuration section](#module-configuration)), the bar can be started using
```bash
ustatus mystatusbar
```
Any bar configuration setting can be overriden with commandline flags; run
```bash
ustatus --help
```
for more details.

The available bar configuration keys are:

{generate_table(bar)}

## Module configuration
All *module configurations* should be under a table called `modules`. For example, a battery meter module called `mymodule` is configured as in the following snippet:
```toml
[modules.mymodule]
type = "battery"
show_label = true
label = "My Battery Module"
```

The available module configuration options are:

{generate_table(module)}
"""
    with open("CONFIGURATION.md", "w") as file:
        file.write(docs)


def generate_table(table):
    bar_table = " Key | Type | Available in command line | Default | Description \n ---|---|---|---|---\n"
    for prop_name, prop_details in table["properties"].items():
        bar_table += f"`{prop_name}` | {generate_type_doc(prop_details)} | {'yes' if cmdline_friendly(prop_details) else 'no'} | `{prop_details.get('default', None)}` | {prop_details.get('description', None)}\n"
    return bar_table


def generate_type_doc(type: Dict) -> str:
    if "enum" in type:
        return _intercalate(map(lambda a: f'`"{a}"`', type["enum"]), " *or* ")
    elif "type" in type:
        return type["type"]
    elif "anyOf" in type:
        return _intercalate(
            map(lambda a: generate_type_doc(a), type["anyOf"]),
            " *or* ",
        )
    else:
        return "unknown"


def _intercalate(l: Iterable[str], sep: str):
    out = ""
    for i, val in enumerate(l):
        if i != 0:
            out += sep
        out += val
    return out
