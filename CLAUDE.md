# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **laser scanning microscope control application** built on the [ScopeFoundry](https://github.com/ScopeFoundry/ScopeFoundry) framework. The app integrates two hardware components: an MCP server for AI-assistant control via Model Context Protocol, and a Git session manager for reproducible experimental sessions.

## Environment & Package Management

This project uses **`uv`** for Python dependency management (Python 3.14 required).

```bash
# Install dependencies
uv sync

# Run the main application
uv run python laser_scanning_app.py

# Or activate the venv first
.venv/Scripts/activate   # Windows
python laser_scanning_app.py
```

Key dependencies: `fastmcp`, `PyQt6`, `pyqtgraph`, `h5py`, `pipython` (PI stage), `pyvisa`, `pyserial`, `numpy`, `matplotlib`.

## Submodules

Three git submodules must be initialized before development:

```bash
git submodule update --init --recursive
```

| Submodule | Path | Purpose |
|-----------|------|---------|
| ScopeFoundry | `ScopeFoundry/` | Core framework (BaseMicroscopeApp, hardware/measurement base classes) |
| mcp_server | `ScopeFoundryHW/mcp_server/` | MCP server hardware component |
| session_manager | `ScopeFoundryHW/session_manager/` | Git-based session management hardware |

## Running Tests

```bash
# MCP server tests
python ScopeFoundryHW/mcp_server/test_mcp_tools.py

# Test apps (require hardware or simulator)
python ScopeFoundryHW/mcp_server/mcp_test_app.py
python ScopeFoundryHW/session_manager/test_app.py
python ScopeFoundryHW/toupcam/test_app.py
python ScopeFoundryHW/asi_stage/asi_stage_test_app.py
python ScopeFoundryHW/mcl_microstage/mcl_microstage_test_app.py
```

## Architecture

### Application Entry Point

`laser_scanning_app.py` subclasses `BaseMicroscopeApp` and registers hardware components in `setup()`. Note: there are two different registration APIs — pass an instance to `add_hardware_component()`, or pass the class to `add_hardware()`:

```python
self.add_hardware_component(MCPServerHardware(self))  # instantiated
self.add_hardware(GitSessionManagerHW)                 # class only
```

### Active Hardware & Measurements (laser_scanning_app.py)

- **Hardware**: 
  - `MCPServerHardware`: Provides MCP interface.
  - `GitSessionManagerHW`: Manages experimental sessions.
  - `MCLMicrostageHW`: Mad City Labs microstage.
  - `ToupCamHW`: ToupCam camera interface.
  - `ActonSpectrometerHW`: Acton spectrometer.
  - `AndorCCDHW`: Andor CCD camera.
- **Measurements**:
  - `MCLMicrostageControlMeasure`: Direct stage control.
  - `ToupCamLiveMeasure`: Live camera feed.
  - `AndorCCDReadoutMeasure`: CCD data acquisition.
  - `MCLAndorHyperSpec2DScan`: Hyperspectral 2D raster scan combining MCL stage and Andor CCD.

### ScopeFoundry Framework Concepts

- **HardwareComponent** (`ScopeFoundry/hardware.py`): Wraps physical instruments. Implement `setup()` (add LoggedQuantities and operations), `connect()`, `disconnect()`.
- **Measurement** (`ScopeFoundry/measurement.py`): Runs in a QThread. Implement `setup()` and `run()` (measurement loop, check `self.interrupt_measurement_called` for stop signal).
- **LoggedQuantity**: A typed, observable value (int, float, bool, str, etc.) that auto-syncs between hardware, GUI widgets, and HDF5 data files. Access via `self.settings.New(...)` and read/write via `lq.val` or `lq.update_value(v)`.
- **Operations**: GUI buttons created with `self.add_operation("Label", callback)`.

### MCP Server Hardware (`ScopeFoundryHW/mcp_server/mcp_server_hw.py`)

Runs a **FastMCP** server on `http://localhost:8000/mcp` in its own QThread (`MCPServerThread`). Exposes the running ScopeFoundry app via these tools:

- `list_logged_quantities` / `get_logged_quantity` / `set_logged_quantity` — read/write app settings; paths use `app.<name>`, `hardware.<hw_name>.<name>`, `measurement.<meas_name>.<name>`
- `list_measurements` / `start_measurement` / `stop_measurement` / `get_measurement_status`
- `execute_python` — runs code in the MCP thread (no GUI access)
- `execute_python_gui` — runs code in the GUI thread via Qt signal/slot; all context vars (`app`, `hardware`, `measurements`, `settings`) are available in both

### Git Session Manager (`ScopeFoundryHW/session_manager/git_session_manager_hw.py`)

Manages experimental sessions as git branches. Branch format: `session-{YYMMDD-HHMMSS}-{session_name}`. On session start:

1. Creates and checks out the new branch.
2. Commits the current state.
3. Creates an annotated git tag `start-{branch_name}`.

## Data Storage

Measurements write HDF5 files to the `data/` directory. Logs go to `log/`. LLM session transcripts go to `llm-sessions/`.

## Code Style & Guidelines

- **Naming**: Use `CamelCase` for classes (Hardware, Measurement), `snake_case` for variables, methods, and file names.
- **Typing**: Use type hints for function arguments and return values where possible.
- **Hardware/Measurement Registration**: Register hardware in `setup()` of the app.
- **Thread Safety**: All Qt widget operations in MCP server must use `execute_python_gui`.
- **Documentation**: Keep `CLAUDE.md` and `MEMORY.md` updated with major architectural changes or new hardware additions.

## Adding New Hardware

1. Create `ScopeFoundryHW/<device_name>/<device_name>_hw.py` subclassing `HardwareComponent`.
2. Implement `setup()` (call `self.settings.New(...)`), `connect()`, `disconnect()`.
3. Register in `laser_scanning_app.py`.

## Adding New Measurements

1. Create a measurement file subclassing `Measurement`.
2. Implement `setup()` and `run()` (check `self.interrupt_measurement_called`).
3. Register in `laser_scanning_app.py`.
