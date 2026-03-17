# MQI Interpreter

This project reads proton therapy log data and generates MOQUI CSV output.

## What It Uses

The current CLI expects:

- One RTPLAN DICOM file (`.dcm`) inside the log directory
- One or more PTN log files (`.ptn`) inside the log directory
- `PlanRange.txt` files inside timestamp subdirectories under the log directory

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main_cli.py --logdir /path/to/logdir --outputdir /path/to/outputdir
```

Example:

```bash
python main_cli.py --logdir ./logs --outputdir ./output
```

## Output

The CLI writes CSV output under the output directory. It also copies the RTPLAN DICOM file into:

```text
outputdir/plan/
```

CSV files are generated per beam and energy layer under subdirectories created by the program.

## Notes

- Machine-specific calibration is loaded automatically from `scv_init_G1.txt` or `scv_init_G2.txt`
- The machine type is detected from `TreatmentMachineName` in the RTPLAN
- For G1 plans, the code may also generate aperture or MLC CSV files
