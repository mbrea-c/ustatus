
# Configuration guide
Configuration is written in [TOML](https://toml.io/en/). Pystatus will read a file called `pystatus.toml` at `$XDG_CONFIG_HOME/pystatus/pystatus.toml` or at `$HOME/.config/pystatus/pystatus.toml` if the former is not defined.

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
pystatus mystatusbar
```
Any bar configuration setting can be overriden with commandline flags; run
```bash
pystatus --help
```
for more details.

The available bar configuration keys are:

 Key | Type | Available in command line | Default | Description 
 ---|---|---|---
`anchors` | `array` | `True` | `None` | None
`output` | `string` | `True` | `None` | Force bar to appear in a given output, or leave empty for auto-choose
`orientation` | `string` | `True` | `None` | None
`modules_start` | `array` | `True` | `[]` | None
`modules_center` | `array` | `True` | `[]` | None
`modules_end` | `array` | `True` | `[]` | None
`exclusive` | `boolean` | `True` | `False` | None
`width` | `|integer|auto` | `False` | `auto` | None
`height` | `|integer|auto` | `False` | `auto` | None
`separators` | `boolean` | `True` | `False` | None


## Module configuration
All *module configurations* should be under a table called `modules`. For example, a battery meter module called `mymodule` is configured as in the following snippet:
```toml
[modules.mymodule]
type = "battery"
show_label = true
label = "My Battery Module"
```

The available module configuration options are:

 Key | Type | Available in command line | Default | Description 
 ---|---|---|---
`type` | `string` | `True` | `None` | None
`show_label` | `boolean` | `True` | `False` | None
`label` | `string` | `True` | `Label` | None
`length` | `integer` | `True` | `25` | None

