# LabOneQ Experiment Library

A collection of Python helpers and Jupyter notebooks for designing, running, analyzing, plotting, and saving quantum-device experiments with Zurich Instruments LabOne Q.

> **Hardware notice:** This repository can build and analyze experiments without hardware in some workflows, but executing an experiment on a real device requires compatible Zurich Instruments hardware, a valid LabOne Q device setup, network access, and the appropriate instrument configuration. The repository does not contain those credentials or device-specific settings.

## What is included

- [`LabOneQ/new_main.ipynb`](LabOneQ/new_main.ipynb) — primary notebook workflow using `laboneq-applications`.
- [`LabOneQ/all_imports.py`](LabOneQ/all_imports.py) — common LabOne Q, fitting, and application imports.
- [`LabOneQ/qelement_helper.py`](LabOneQ/qelement_helper.py) — quantum-element classes, parameters, and calibration helpers for transmons, fluxonium, and related elements.
- [`LabOneQ/qops_helper.py`](LabOneQ/qops_helper.py) — operation helpers built on the quantum-element definitions.
- [`LabOneQ/qubit_experiments.py`](LabOneQ/qubit_experiments.py) — experiment construction and qubit experiment workflows.
- [`LabOneQ/analysis_helper.py`](LabOneQ/analysis_helper.py) — fitting, analysis, and result-processing helpers.
- [`LabOneQ/plot_helper.py`](LabOneQ/plot_helper.py) — interactive Plotly renderers for LabOne Q results.
- [`LabOneQ/helper.py`](LabOneQ/helper.py) — data-directory, artifact-saving, and result-manifest utilities.
- [`LabOneQ/utils/resonator_fitting.py`](LabOneQ/utils/resonator_fitting.py) — resonator fitting routines.
- [`LabOneQ/device_description/`](LabOneQ/device_description/) — example device-description files; select and adapt one for your device.
- [`LabOneQ/archive/`](LabOneQ/archive/) — older notebooks and experiments kept for reference.

The helper modules currently use local imports such as `from helper import *`. Run notebooks with [`LabOneQ/`](LabOneQ/) as the working directory, or add that directory to Python's import path.

## Installation

### Option A: Conda environment (recommended)

From the repository root:

```powershell
conda env create -f environment.yml
conda activate laboneq-repo
```

The environment file installs Conda-managed numerical/Jupyter/Qt packages and pip-installed LabOne Q, Zurich Instruments, QCoDeS, plotting, fitting, instrument-control, and test packages.

To update an existing environment after dependency changes:

```powershell
conda env update -f environment.yml --prune
```

### Option B: Existing Python environment with pip

Use Python 3.12 or another version supported by the installed LabOne Q release. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS/Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

The single source of truth for pip dependencies is [`requirements.txt`](requirements.txt). The former plotting-only file, [`LabOneQ/requirements-plotting.txt`](LabOneQ/requirements-plotting.txt), is retained only as a pointer to the root requirements file.

### Start Jupyter

After activating the environment:

```powershell
jupyter lab
```

Open [`LabOneQ/new_main.ipynb`](LabOneQ/new_main.ipynb). Set the notebook's working directory to [`LabOneQ/`](LabOneQ/) so imports such as `helper`, `qelement_helper`, and `qubit_experiments` resolve correctly.

If using VS Code, select the `laboneq-repo` Conda interpreter or the `.venv` interpreter as the notebook kernel.

## Typical workflow

### 1. Configure the device

Start with a device description in [`LabOneQ/device_description/`](LabOneQ/device_description/). These files are examples and must be checked against the actual wiring, signal names, channels, oscillator frequencies, delays, ranges, and qubit parameters of the target setup.

Do not commit passwords, API keys, private IP addresses, or other sensitive connection information. Keep local connection settings outside version control when possible.

### 2. Import the project helpers

When working from the [`LabOneQ/`](LabOneQ/) directory, the common workflow is:

```python
from all_imports import *
from helper import data_directory_update, save_experiment_results
from qelement_helper import Transmon
from qops_helper import *
from qubit_experiments import *
```

The exact constructors and experiment functions depend on the selected notebook and device model. Inspect the function signatures and nearby notebook cells before adapting a workflow to a new device.

### 3. Build or load a LabOne Q session

Use the LabOne Q session and device-setup patterns from [`LabOneQ/new_main.ipynb`](LabOneQ/new_main.ipynb) and the official LabOne Q documentation. A session generally requires a device setup, signal mapping, calibration, and an experiment definition. For development, use emulation where supported before connecting to hardware.

A minimal conceptual flow is:

```python
from laboneq.simple import Session

# Build or load your device setup and experiment here.
# device_setup = ...
# experiment = ...
# calibration = ...

# session = Session(device_setup)
# session.connect(do_emulation=True)
# results = session.run(experiment)
```

The commented example is intentionally incomplete because device setup and signal wiring are hardware-specific.

### 4. Analyze and plot results

The plotting helpers return Plotly figures. For example, after obtaining a compatible experiment and session result:

```python
from plot_helper import plot_local_resonator_trace

figure = plot_local_resonator_trace(experiment, session, qubit)
figure.show()
```

The plot functions expect the LabOne Q experiment, session, and quantum-element objects to contain the signal and calibration fields used by the selected experiment. See [`LabOneQ/plot_helper.py`](LabOneQ/plot_helper.py) for the available renderers and expected arguments.

For fitting and numerical analysis, use [`LabOneQ/analysis_helper.py`](LabOneQ/analysis_helper.py) and [`LabOneQ/utils/resonator_fitting.py`](LabOneQ/utils/resonator_fitting.py).

### 5. Save results

[`LabOneQ/helper.py`](LabOneQ/helper.py) provides helpers for date-based data directories and collision-safe artifact names. The result-saving workflow records raw results and a manifest so repeated configurations can be identified:

```python
from helper import save_experiment_results

manifest_entry = save_experiment_results(
    results,
    experiment,
    qubit,
    data_root="data",
    metadata={"notes": "example run"},
)
```

By default, results are placed below `data/YYYY-MM-DD/<qubit>/<experiment>/`. Existing artifacts are not overwritten. Confirm the generated files and metadata before deleting or moving data.

## Hardware and instrument control

The repository contains optional integrations for:

- Zurich Instruments LabOne Q and `zhinst` packages.
- QCoDeS drivers for Yokogawa GS200 sources and Rohde & Schwarz SGS100A sources.
- PyVISA-based oscilloscope control in [`LabOneQ/utils/Oscilloscope_control.ipynb`](LabOneQ/utils/Oscilloscope_control.ipynb).

These integrations require hardware-specific VISA resources, network configuration, drivers, and permissions. Installing the Python package does not install vendor firmware, instrument drivers, or configure the hardware.

## Testing and validation

Run the available tests from the repository root:

```powershell
python -m pytest
```

For a quick import check:

```powershell
python -c "import laboneq; import numpy; import scipy; import plotly; print('Environment looks usable')"
```

For hardware-independent development, first validate imports, device-description parsing, experiment construction, and emulated execution. Only then run against connected instruments.

## Troubleshooting

### `ModuleNotFoundError` for local helper modules

Run Jupyter from the repository root and set the notebook working directory to [`LabOneQ/`](LabOneQ/), or add the directory explicitly:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "LabOneQ"))
```

### LabOne Q or `zhinst` version conflicts

Use the pinned versions in [`requirements.txt`](requirements.txt) and recreate the environment rather than mixing packages into an older environment:

```powershell
conda env remove -n laboneq-repo
conda env create -f environment.yml
```

### Qt or interactive plotting problems

Confirm that the environment contains the Qt package installed by [`environment.yml`](environment.yml), restart the Jupyter kernel, and use a supported Matplotlib backend. Plotly figures can generally be displayed with `figure.show()` without a Qt backend.

### Hardware connection failures

Check instrument power, network/VISA addressing, firewall rules, LabOne server availability, device identifiers, and the signal mapping in the device setup. Connection details are setup-specific and cannot be inferred from this repository.

## Reproducibility notes

- Record the environment file and Git commit used for each measurement campaign.
- Keep device descriptions and calibration values synchronized with the physical setup.
- Store run metadata with each result.
- Do not treat archived notebooks as the current API; prefer [`LabOneQ/new_main.ipynb`](LabOneQ/new_main.ipynb) and the current helper modules.
- Review all experiment parameters and safety limits before applying signals to hardware.

## License and attribution

No license file is currently included in this repository. Add the project's intended license and attribution requirements before distributing the code outside the owning organization.
