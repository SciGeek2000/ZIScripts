# plotting and fitting functionality

# from laboneq.analysis.fitting import (
#     lorentzian,
#     oscillatory,
#     oscillatory_decay,
#     exponential_decay,
# )

from pathlib import Path
import datetime
from datetime import date, timezone
import hashlib
import json
import os
import re
import tempfile
import numpy as np
from scipy.stats import linregress

def data_directory_update():
    date = datetime.date.today()
    datadir = Path('data/' + str(date) + '/')
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    return datadir
datadir = data_directory_update()

def live_plotter(fig, new_data):
    pass

def non_redund_save_fig(fig, name):
# A function to prevent figure overwrite issues
    datadir = data_directory_update()
    i = 1
    while True:
        fig_name = Path(str(datadir) + f'/{name}_{i}.png')
        if os.path.isfile(fig_name) is False:
            fig_name = Path(str(datadir) + f'/{name}_{i}')
            fig.savefig(fig_name)
            break
        else:
            i = i+1

def non_redund_save_pd(pd_data, name):
    datadir = data_directory_update()
    i = 1
    while True:
        pd_name = Path(str(datadir) + f'/{name}_{i}.csv')
        if os.path.isfile(pd_name) is False:
            pd_name = Path(str(datadir) + f'/{name}_{i}.csv')
            pd_data.to_csv(pd_name)
            break
        else:
            i += 1

def non_redund_save_csv(csv_data, name):
    datadir = data_directory_update()
    i = 1
    while True:
        csv_name = Path(str(datadir) + f'/{name}_{i}.csv')
        if os.path.isfile(csv_name) is False:
            csv_name = Path(str(datadir) + f'/{name}_{i}.csv')
            csv_data.to_csv(csv_name)
            break
        else:
            i += 1

def _safe_result_name(name):
    """Return a filesystem-safe name for a qubit or experiment UID."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(name)).strip("._")
    return name or "unnamed"


def _json_default(value):
    """Convert common LabOne Q and NumPy values into JSON-compatible values."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "uid"):
        return str(value.uid)
    return str(value)


def _configuration_metadata(exp, qubit, metadata=None):
    """Build the deterministic metadata used to identify repeated configurations."""
    experiment_uid = getattr(exp, "uid", type(exp).__name__)
    qubit_uid = getattr(qubit, "uid", str(qubit))
    configuration = {
        "qubit": str(qubit_uid),
        "experiment": str(experiment_uid),
    }

    # The serialized experiment captures sweep values and other definition-level
    # settings without requiring changes to each experiment builder.
    try:
        from laboneq.serializers import to_dict
        configuration["experiment_definition"] = to_dict(exp)
    except Exception:
        configuration["experiment_definition"] = str(exp)

    if metadata is not None:
        configuration["metadata"] = metadata

    return configuration


def _configuration_fingerprint(configuration):
    canonical = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_manifest(manifest_path):
    if not manifest_path.exists():
        return {"format_version": 1, "runs": []}

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, dict) or not isinstance(manifest.get("runs"), list):
        raise ValueError(f"Invalid result manifest: {manifest_path}")
    manifest.setdefault("format_version", 1)
    return manifest


def _write_manifest(manifest_path, manifest):
    """Replace the manifest atomically so an interrupted write cannot corrupt it."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=manifest_path.parent,
            prefix=f".{manifest_path.stem}_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(manifest, temporary_file, indent=2, sort_keys=True)
            temporary_file.write("\n")
        os.replace(temporary_path, manifest_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _reserve_artifact_path(directory, stem, extension):
    """Reserve a unique artifact path using exclusive file creation."""
    counter = 0
    while True:
        suffix = "" if counter == 0 else f"_{counter}"
        artifact_path = directory / f"{stem}{suffix}.{extension}"
        try:
            file_descriptor = os.open(
                artifact_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.close(file_descriptor)
            return artifact_path
        except FileExistsError:
            counter += 1


def _reserve_result_path(directory, stem):
    """Reserve a unique result path using exclusive file creation."""
    return _reserve_artifact_path(directory, stem, "json")


def save_experiment_results(
    results,
    exp,
    qubit,
    data_root="data",
    metadata=None,
    timestamp=None,
):
    """Save a successful LabOne Q result and index it in the run manifest.

    Every call writes a raw JSON result, including repeated configurations. The
    returned manifest entry marks repeats using the configuration fingerprint.
    """
    timestamp = timestamp or datetime.datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)

    experiment_uid = str(getattr(exp, "uid", type(exp).__name__))
    qubit_uid = str(getattr(qubit, "uid", qubit))
    configuration = _configuration_metadata(exp, qubit, metadata)
    fingerprint = _configuration_fingerprint(configuration)

    root = Path(data_root)
    date_directory = root / timestamp.date().isoformat()
    result_directory = date_directory / _safe_result_name(qubit_uid) / _safe_result_name(experiment_uid)
    result_directory.mkdir(parents=True, exist_ok=True)

    run_id = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    result_stem = f"{_safe_result_name(experiment_uid)}_{run_id}"
    result_path = _reserve_result_path(result_directory, result_stem)
    temporary_result_path = result_path.with_name(f".{result_path.name}.tmp")

    try:
        from laboneq.simple import save as laboneq_save
        laboneq_save(results, temporary_result_path)
        os.replace(temporary_result_path, result_path)
    except Exception:
        if temporary_result_path.exists():
            temporary_result_path.unlink()
        if result_path.exists():
            result_path.unlink()
        raise

    manifest_path = root / "manifest.json"
    manifest = _load_manifest(manifest_path)
    previous_run = next(
        (run for run in manifest["runs"] if run.get("fingerprint") == fingerprint),
        None,
    )
    relative_result_path = result_path.relative_to(root).as_posix()
    entry = {
        "run_id": run_id,
        "qubit": qubit_uid,
        "experiment": experiment_uid,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "result_path": relative_result_path,
        "fingerprint": fingerprint,
        "duplicate": previous_run is not None,
        "duplicate_of": previous_run.get("run_id") if previous_run else None,
        "configuration": configuration,
    }
    manifest["runs"].append(entry)
    _write_manifest(manifest_path, manifest)
    return entry


def _save_derived_artifact(raw_run, artifact_writer, artifact_name, extension, artifact_type, data_root="data"):
    """Save an artifact next to its raw result and link it in the manifest."""
    run_id = raw_run.get("run_id")
    if not run_id:
        raise ValueError("raw_run must be an entry returned by save_experiment_results")

    root = Path(data_root)
    result_path = root / Path(raw_run["result_path"])
    if not result_path.exists():
        raise FileNotFoundError(f"Raw result does not exist: {result_path}")

    artifact_directory = result_path.parent / "artifacts"
    artifact_directory.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_result_name(artifact_name)
    artifact_path = _reserve_artifact_path(
        artifact_directory,
        f"{safe_name}_{run_id}",
        extension,
    )
    temporary_path = artifact_path.with_name(f".{artifact_path.name}.tmp")

    try:
        artifact_writer(temporary_path)
        os.replace(temporary_path, artifact_path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        if artifact_path.exists():
            artifact_path.unlink()
        raise

    manifest_path = root / "manifest.json"
    manifest = _load_manifest(manifest_path)
    manifest_run = next(
        (run for run in manifest["runs"] if run.get("run_id") == run_id),
        None,
    )
    if manifest_run is None:
        artifact_path.unlink(missing_ok=True)
        raise ValueError(f"Run {run_id} is not present in {manifest_path}")

    artifact_entry = {
        "type": artifact_type,
        "name": safe_name,
        "format": extension,
        "path": artifact_path.relative_to(root).as_posix(),
    }
    manifest_run.setdefault("artifacts", []).append(artifact_entry)
    _write_manifest(manifest_path, manifest)
    return artifact_entry


def save_figure_artifact(fig, raw_run, name="plot", data_root="data", format="png"):
    """Save a figure linked to a previously saved raw run."""
    format = format.lower().lstrip(".")
    if format not in {"png", "pdf", "svg"}:
        raise ValueError("format must be one of: png, pdf, svg")

    return _save_derived_artifact(
        raw_run,
        lambda path: fig.savefig(path, format=format),
        name,
        format,
        "figure",
        data_root,
    )


def save_table_artifact(table, raw_run, name="table", data_root="data"):
    """Save a table linked to a previously saved raw run as CSV."""
    def write_table(path):
        if hasattr(table, "to_csv"):
            table.to_csv(path)
        else:
            np.savetxt(path, np.asarray(table), delimiter=",", fmt="%s")

    return _save_derived_artifact(
        raw_run,
        write_table,
        name,
        "csv",
        "table",
        data_root,
    )


def remove_local_phase_delay(IQ_data: np.ndarray, frequency: np.ndarray, delay):
    '''Removes IQ bias, zeros phase delay (unique to that sweep), and returns data as cleaned IQ arrays'''
    IQ_data = IQ_data #- np.mean(IQ_data)
    cleaned_complex = np.exp(1j*delay*2*np.pi*frequency)*IQ_data
    return cleaned_complex

# The procedure I will follow for phase will be:
#   1.) Center the IQ blob by just removing the average of the data. NOTE! This was not something I was doing and accounts for net assymetric chain/mesurement.
#   2.) Find the np.angle and np.unwrap of the data.
#   3.) Find a linear fit for this region. This may be a slighly different electrical delay due to the TWPA's local frequency phase delay.
#   4.) Subtract out the linear phase background. NOTE! Do not then zero this phase data.
#   5.) Plot this data. This should then form nice circles in IQ space associated with the resonator itself.