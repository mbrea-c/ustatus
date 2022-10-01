# ustatus

_NOTE: Previously named pystatus, renamed due to a PyPI project naming conflict
preventing me from publishing the project._

Configurable status window and/or bar for wayland compositors with support for
the wlr-layer-shell protocol.

![Screenshot closed](pystatus_closed.png)
![Screenshot cpu meters](pystatus_cpu.png)
![Screenshot power-profiles-daemon](pystatus_ppd.png)
![Screenshot powermenu](pystatus_power.png)

## Features

- TOML configuration.
  - Supports configuration of different bars, and choice of bar at startup with
    commandline argument.
- A variety of built-in modules:
  - System tray module ([StatusNotifierItem protocol](https://www.freedesktop.org/wiki/Specifications/StatusNotifierItem/)), with Dbusmenu.
  - Cpu monitor module, with usage graphs.
  - MPRIS module.
  - Battery module.
  - Volume module.
  - [power-profiles-daemon](https://gitlab.freedesktop.org/hadess/power-profiles-daemon) remote module.
- Remote interface through dbus, currently allowing:
  - Show/hide/toggle bar or status window.

## Running without installing

The project is built using [Poetry](https://python-poetry.org/).
To run, clone the project

```
git clone https://github.com/mbrea-c/ustatus.git
```

move to the cloned directory

```
cd ustatus
```

install dependencies in a local venv with

```
poetry install
```

and run ustatus with

```
poetry run ustatus <bar name>
```

## User-wide installation from source

The project is built using [Poetry](https://python-poetry.org/).

To build
locally, clone the project

```
git clone https://github.com/mbrea-c/ustatus.git
```

move to the cloned directory

```
cd ustatus
```

and build

```
poetry build
```

This will create two files in the `dist` directory,

```
dist/ustatus-<version_number>.tar.gz
dist/ustatus-<version_number>-py3-none-any.whl
```

For a user-wide installation, run

```
cd dist
pip install --upgrade ustatus-<version_number>.tar.gz
```

## Configuration

See the [configuration guide](CONFIGURATION.md) for details. An example configuration file can be
found in [examples/ustatus.toml](examples/ustatus.toml)

## Is this in an usable state?

I think so, I have used (and still use) this in my daily-driver machine for about 6 months.
However, there are currently some limitations that some might consider deal
breaking:

- The UI respects the system GTK theme, but it is not possible to do separate
  custom theming at the moment. I'm thinking of adding some form of this soon though, as GTK
  allows theming using CSS fairly easily.
- In my daily driver setup I use a status window anchored to the right side of
  the screen, so I haven't done a lot of testing with a horizontal status _bar_.
  It is possible, but there might (will) be bugs and rough edges. I'm willing to
  work on this if there is interest.
