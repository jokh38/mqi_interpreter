import csv
import pathlib
import re
from typing import Dict, List

import numpy as np

from generators.plan_timing import build_layer_time_trajectory


def _is_setup_beam(beam_data: dict) -> bool:
    beam_name = beam_data.get("beam_name", "")
    return beam_name == "SETUP" or beam_data.get("is_setup_field", False)


def _sanitize_beam_name(beam_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", beam_name)


def _extract_spot_layers(control_point_details: List[Dict]) -> List[Dict]:
    spot_layers = []

    for cp_detail in control_point_details:
        positions = cp_detail.get("scan_spot_positions") or []
        weights = cp_detail.get("scan_spot_meterset_weights") or []
        if not positions and not weights:
            continue
        if len(positions) % 2 != 0:
            raise ValueError("Plan spot position map must contain x/y pairs.")
        if len(positions) // 2 != len(weights):
            raise ValueError(
                "Plan spot position and meterset weight counts do not match."
            )

        spot_layers.append(
            {
                "energy": float(cp_detail.get("energy")),
                "positions": np.asarray(positions, dtype=float).reshape(-1, 2),
                "weights": np.asarray(weights, dtype=float),
            }
        )

    return spot_layers


def _weights_to_mu(weights: np.ndarray, total_mu_for_layer: float) -> np.ndarray:
    total_weight = float(np.sum(weights))
    if total_weight > 0:
        return weights / total_weight * float(total_mu_for_layer)
    return np.zeros(len(weights), dtype=float)


def _resample_plan_layer_to_timegain(
    positions_mm: np.ndarray,
    mu_per_spot: np.ndarray,
    energy: float,
    time_gain_ms: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    trajectory = build_layer_time_trajectory(
        positions_cm=positions_mm * 0.1,
        mu=mu_per_spot,
        energy=energy,
    )

    spot_time_s = np.asarray(trajectory["time_axis_s"], dtype=float)
    spot_x_mm = np.asarray(trajectory["x_cm"], dtype=float) * 10.0
    spot_y_mm = np.asarray(trajectory["y_cm"], dtype=float) * 10.0
    spot_cumulative_mu = np.cumsum(mu_per_spot, dtype=float)

    dt_s = float(time_gain_ms) / 1000.0
    if dt_s <= 0:
        raise ValueError("time_gain_ms must be positive for plan resampling.")

    t_end_s = float(spot_time_s[-1]) if spot_time_s.size else 0.0
    sample_time_s = np.arange(0.0, t_end_s + dt_s * 0.5, dt_s, dtype=float)
    if sample_time_s.size == 0:
        sample_time_s = np.array([0.0], dtype=float)

    sample_x_mm = np.interp(sample_time_s, spot_time_s, spot_x_mm)
    sample_y_mm = np.interp(sample_time_s, spot_time_s, spot_y_mm)
    sample_cumulative_mu = np.interp(sample_time_s, spot_time_s, spot_cumulative_mu)
    sample_mu = np.diff(sample_cumulative_mu, prepend=0.0)

    return sample_time_s * 1000.0, sample_x_mm, sample_y_mm, sample_mu


def get_monitor_range_factor(monitor_range_code: int) -> float:
    """
    Determines the monitorRangeFactor based on the monitor_range_code.
    Codes and values from C++ Moqui code options.
    """
    if monitor_range_code == 2:
        return 1.0
    elif monitor_range_code == 3:
        return 2.978723404255319
    elif monitor_range_code == 4:
        return 8.936170212765957
    elif monitor_range_code == 5:
        return 26.80851063829787
    else:
        # Default or error based on strictness. C++ code defaults to 1.0 if not recognized.
        print(
            f"Warning: Unrecognized monitor_range_code {monitor_range_code}. Defaulting factor to 1.0."
        )
        return 1.0


def generate_moqui_csvs(
    rt_plan_data: Dict,
    ptn_data_list: List[Dict],
    dose_monitor_ranges: List[int],
    output_base_dir: str,
    dose_dividing_factor: int = 1,
):
    """
    Generates CSV files for MOQUI based on RTPLAN and processed PTN log data.
    Uses log-based approach: directly uses time, position, and MU data from PTN files.

    Args:
        rt_plan_data: Dictionary containing parsed RTPLAN data.
        ptn_data_list: List of dictionaries, where each dictionary is the
                       output of parse_ptn_file, corresponding to an energy layer.
        dose_monitor_ranges: List of integers representing monitor range codes,
                             corresponding to each energy layer.
        output_base_dir: Base directory for creating output files.
        dose_dividing_factor: Factor to divide dose values (default: 1).

    Raises:
        KeyError: If essential keys are missing from input data.
        IndexError: If ptn_data_list or dose_monitor_ranges are shorter than
                    the total number of energy layers.
        IOError: If directory or file creation fails.
    """
    try:
        beams = rt_plan_data["beams"]
    except KeyError as e:
        raise KeyError(f"Error: Missing essential key {e} in rt_plan_data.")

    # Create directory for log-based MOQUI CSV data
    base_dir = pathlib.Path(output_base_dir)
    log_base_dir = base_dir / "log"

    global_data_idx = 0

    for beam_idx, beam in enumerate(beams):
        try:
            beam_name = beam["beam_name"]
            beam_name = _sanitize_beam_name(beam_name)
            energy_layers = beam["energy_layers"]
            is_setup_field = beam.get("is_setup_field", False)
        except KeyError as e:
            raise KeyError(
                f"Error: Missing essential key {e} in beam data for beam index {beam_idx}."
            )

        if _is_setup_beam(beam):
            continue

        log_field_dir = log_base_dir / beam_name
        try:
            log_field_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Error creating directory {log_field_dir}: {e}")

        for layer_idx_in_beam, energy_layer in enumerate(energy_layers):
            if global_data_idx >= len(ptn_data_list):
                print(
                    f"Warning: Not enough PTN data entries. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(ptn_data_list)} PTN data entries provided. Skipping remaining layers."
                )
                break
            if global_data_idx >= len(dose_monitor_ranges):
                print(
                    f"Warning: Not enough dose monitor range codes. Needed for layer {global_data_idx + 1}, "
                    f"but only {len(dose_monitor_ranges)} codes provided. Skipping remaining layers."
                )
                break

            ptn_data = ptn_data_list[global_data_idx]
            monitor_range_code = dose_monitor_ranges[global_data_idx]

            try:
                nominal_energy = float(energy_layer["nominal_energy"])
                # MU from rt_plan_data["energy_layers"]["mu"] is the total MU for this layer,
                # not used directly in this CSV generation per log point, but for context.

                dose1_au = ptn_data[
                    "dose1_au"
                ]  # This is an array of MU counts from the log for each time point
                time_ms = ptn_data["time_ms"]
                x_mm = ptn_data["x_mm"]
                y_mm = ptn_data["y_mm"]
            except KeyError as e:
                raise KeyError(
                    f"Error: Missing essential key {e} in PTN data for layer index {global_data_idx} "
                    f"(Beam {beam_idx + 1}, Layer in beam {layer_idx_in_beam + 1})."
                )
            except TypeError as e:  # For float(nominal_energy) if it's not convertible
                raise ValueError(
                    f"Error: Could not convert nominal_energy to float for layer index {global_data_idx}. Value: {energy_layer.get('nominal_energy')}. Error: {e}"
                )

            monitor_range_factor = get_monitor_range_factor(monitor_range_code)

            # Match the original C++ MOQUIThread:
            # apply monitor range scaling and dose dividing only at CSV generation.
            corrected_mu = dose1_au.astype(float)

            # Apply monitor range factor
            corrected_mu *= monitor_range_factor

            # Apply dose dividing factor
            corrected_mu = corrected_mu / dose_dividing_factor

            # Round to integers
            corrected_mu = np.round(corrected_mu).astype(int)

            # Prepare CSV Data
            # Ensure all arrays are 1D and have the same length
            if not (
                time_ms.ndim == 1
                and x_mm.ndim == 1
                and y_mm.ndim == 1
                and corrected_mu.ndim == 1
                and len(time_ms) == len(x_mm) == len(y_mm) == len(corrected_mu)
            ):
                raise ValueError(
                    f"Dimension mismatch in data for CSV generation for layer index {global_data_idx}. "
                    f"Shapes: time_ms={time_ms.shape}, x_mm={x_mm.shape}, y_mm={y_mm.shape}, corrected_mu={corrected_mu.shape}"
                )

            # CSV Filename
            csv_file_name = f"{layer_idx_in_beam + 1:02d}_{nominal_energy:.2f}MeV.csv"

            # Write Log CSV (with monitor range factor)
            log_csv_path = log_field_dir / csv_file_name
            log_csv_rows = zip(time_ms, x_mm, y_mm, corrected_mu)
            try:
                with open(log_csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(log_csv_rows)
            except IOError as e:
                raise IOError(f"Error writing Log CSV file {log_csv_path}: {e}")
            except Exception as e:
                raise RuntimeError(
                    f"An unexpected error occurred while writing Log CSV {log_csv_path}: {e}"
                )

            global_data_idx += 1

    # Final check to ensure all ptn_data and dose_monitor_ranges were consumed if expected
    total_layers_in_plan = sum(
        len(beam.get("energy_layers", [])) for beam in beams if not _is_setup_beam(beam)
    )
    if global_data_idx != total_layers_in_plan:
        print(
            f"Warning: Number of processed layers ({global_data_idx}) does not match "
            f"total energy layers in RTPLAN ({total_layers_in_plan}). "
            f"Ensure ptn_data_list and dose_monitor_ranges match the plan structure."
        )


def generate_plan_csvs(
    rt_plan_data: Dict,
    output_base_dir: str,
    time_gain_ms: float,
    normalization_factor: float | None = None,
):
    """
    Generate plan-derived CSV files directly from RTPLAN scan spot data.

    Each CSV row contains synthetic time, planned x/y position, and planned
    scan spot meterset weight for one spot. Files are written under plan/.
    """
    try:
        beams = rt_plan_data["beams"]
    except KeyError as e:
        raise KeyError(f"Error: Missing essential key {e} in rt_plan_data.")

    base_dir = pathlib.Path(output_base_dir)
    plan_base_dir = base_dir / "plan"

    for beam_idx, beam in enumerate(beams):
        try:
            beam_name = _sanitize_beam_name(beam["beam_name"])
            energy_layers = beam["energy_layers"]
            control_point_details = beam["control_point_details"]
        except KeyError as e:
            raise KeyError(
                f"Error: Missing essential key {e} in beam data for beam index {beam_idx}."
            )

        if _is_setup_beam(beam):
            continue

        plan_field_dir = plan_base_dir / beam_name
        try:
            plan_field_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Error creating directory {plan_field_dir}: {e}")

        spot_layers = _extract_spot_layers(control_point_details)

        if len(spot_layers) < len(energy_layers):
            print(
                f"Warning: Beam {beam_name} has {len(energy_layers)} energy layers but only "
                f"{len(spot_layers)} control points with scan spot data."
            )

        for layer_idx_in_beam, energy_layer in enumerate(energy_layers):
            if layer_idx_in_beam >= len(spot_layers):
                break

            try:
                nominal_energy = float(energy_layer["nominal_energy"])
            except (KeyError, TypeError, ValueError) as e:
                raise ValueError(
                    f"Error: Could not convert nominal_energy for beam {beam_name}, "
                    f"layer {layer_idx_in_beam + 1}. Error: {e}"
                )

            spot_layer = spot_layers[layer_idx_in_beam]
            positions = spot_layer["positions"]
            weights = spot_layer["weights"]
            layer_mu = float(energy_layer.get("mu", 0.0))
            mu_per_spot = _weights_to_mu(weights, layer_mu)
            time_ms, x_mm, y_mm, sample_mu = _resample_plan_layer_to_timegain(
                positions_mm=positions,
                mu_per_spot=mu_per_spot,
                energy=nominal_energy,
                time_gain_ms=time_gain_ms,
            )
            if normalization_factor is not None:
                if normalization_factor <= 0:
                    raise ValueError("normalization_factor must be positive.")
                sample_mu = sample_mu / float(normalization_factor)
                sample_mu = np.round(sample_mu).astype(int)

            csv_file_name = f"{layer_idx_in_beam + 1:02d}_{nominal_energy:.2f}MeV.csv"
            plan_csv_path = plan_field_dir / csv_file_name
            plan_csv_rows = zip(time_ms, x_mm, y_mm, sample_mu)

            try:
                with open(plan_csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(plan_csv_rows)
            except IOError as e:
                raise IOError(f"Error writing Plan CSV file {plan_csv_path}: {e}")
            except Exception as e:
                raise RuntimeError(
                    f"An unexpected error occurred while writing Plan CSV {plan_csv_path}: {e}"
                )


if __name__ == "__main__":
    pass
