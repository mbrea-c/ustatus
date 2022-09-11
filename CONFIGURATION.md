
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
 ---|---|---|---|---
`anchors` | array | yes | `None` | None
`output` | string | yes | `None` | Force bar to appear in a given output, or leave empty for auto-choose
`orientation` | string | yes | `None` | None
`modules_start` | array | yes | `[]` | None
`modules_center` | array | yes | `[]` | None
`modules_end` | array | yes | `[]` | None
`exclusive` | boolean | yes | `False` | None
`width` |  integer *or* `"auto"` | no | `auto` | None
`height` |  integer *or* `"auto"` | no | `auto` | None
`separators` | boolean | yes | `False` | None


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
 ---|---|---|---|---
`type` | string | yes | `None` | None
`show_label` | boolean | yes | `False` | None
`label` | string | yes | `Label` | None
`length` | integer | yes | `25` | None

