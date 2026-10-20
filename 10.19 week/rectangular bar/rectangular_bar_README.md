# Rectangular Bar: Progress and Run Guide

**Xiyang Qiu | Updated October 20, 2026**

Start with **[`json_version/`](json_version/)**. This is the current working example. It reads dimensions from JSON, builds a rectangular bar, and exports STEP and STL files. The Python script can be reused after changing only the JSON input.

## What I completed

- Used Text to CAD and its build123d-based workflow to create a rectangular bar template.
- Connected the template to a JSON input with length, width, height, and units.
- Generated STEP and STL files and checked the saved files for dimensions, volume, and solid/mesh validity.
- Changed the length from 100 to 150 mm and rebuilt the model with the same Python source.
- Tested other dimensions, decimal values, invalid inputs, and recovery after an invalid input.
- Saved example inputs, exported models, previews, logs, validation reports, and short run instructions.

The current input and output files in `json_version/` are **150 x 20 x 10 mm**, with a volume of **30,000 mm^3**.

## How to read this folder

| File or folder | Purpose |
| --- | --- |
| [`json_version/rectangular_bar.py`](json_version/rectangular_bar.py) | Main script. Run this to build and validate the model. |
| [`json_version/dimensions.json`](json_version/dimensions.json) | Editable dimension input. Start here to change the model. |
| [`json_version/validate_geometry.py`](json_version/validate_geometry.py) | Validation helper called by the main script. Keep it beside the main script. |
| [`json_version/requirements.txt`](json_version/requirements.txt) | Python dependency pin: `cadgen==0.7.10`. |
| [`json_version/rectangular_bar.step`](json_version/rectangular_bar.step) | Current solid CAD model. |
| [`json_version/rectangular_bar.stl`](json_version/rectangular_bar.stl) | Current triangle mesh. Select millimeters when importing it into other software. |
| [`json_version/rectangular_bar_validation.json`](json_version/rectangular_bar_validation.json) | Results for the latest run, including input dimensions, measurements, and `passed`. |
| [`json_version/test_150x20x10/`](json_version/test_150x20x10/) | Saved record of the first length-change test, including a [preview](json_version/test_150x20x10/preview.png). |
| [`json_version/test_suite_5_cases/summary.md`](json_version/test_suite_5_cases/summary.md) | Summary of five additional tests and one recovery run. Each case has its own records. |
| `rectangular_bar.py`, `.step`, and `.stl` in this parent folder | Original fixed-size 100 x 20 x 10 mm example. |

For the editable workflow, use the files directly inside `json_version/`. The test subfolders are saved examples and evidence of earlier runs.

## Input format

Edit `json_version/dimensions.json`:

```json
{
  "units": "mm",
  "length": 150,
  "width": 20,
  "height": 10
}
```

| Field | Meaning | Requirement |
| --- | --- | --- |
| `units` | Length unit | Must be `"mm"`. |
| `length` | Size along X | Positive, finite number. |
| `width` | Size along Y | Positive, finite number. |
| `height` | Size along Z | Positive, finite number. |

All four fields are required. Decimal dimensions are supported. Strings, booleans, zero, negative values, and non-finite numbers are rejected. The minimum X/Y/Z corner of the bar is at the origin.

## Run the example

The tested environment is **Windows, Python 3.13, and cadgen 0.7.10**. Clone or download the repository and keep the original filenames together.

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed, open PowerShell at the repository root and run:

```powershell
cd "10.19 week/rectangular bar/json_version"
uv venv --python 3.13 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe rectangular_bar.py
```

The environment setup and dependency installation are needed once. After editing `dimensions.json`, run the same script again:

```powershell
.\.venv\Scripts\python.exe rectangular_bar.py
```

On macOS/Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe` in the installation and run commands. These platforms have not been tested in this work.

If a Python environment already contains the pinned dependency, the main command is simply `python rectangular_bar.py`. The script locates its JSON and output files relative to its own location.

## Read the result

A successful run updates `rectangular_bar.step`, `rectangular_bar.stl`, and `rectangular_bar_validation.json` in `json_version/`.

Open the validation report and check:

1. `input_dimensions` matches the requested JSON dimensions.
2. `step` and `stl` contain the measured dimensions and volume.
3. The top-level `passed` value is `true`.

The volume should equal `length * width * height`. The main script returns exit code `0` on success, `2` for an input configuration error, and `1` for a generation or validation failure. The error messages currently use Chinese and identify the relevant field.

A failed run can leave earlier STEP/STL files in place. Read the latest report and exit code before using the output. A report with `passed: false` does not validate the current input.

## Tests completed

The same JSON-driven Python source was used throughout these tests.

| Test | Expected result | Recorded result |
| --- | --- | --- |
| 80 x 30 x 5 mm | Valid model; 12,000 mm^3 | Passed. |
| 50.5 x 10 x 2 mm | Valid model; 1,010 mm^3 | Passed. |
| `length = 0` | Clear input error; exit code 2 | Rejected as expected. |
| `width = -20` | Clear input error; exit code 2 | Rejected as expected. |
| Missing `height` | Clear input error; exit code 2 | Rejected as expected. |
| Restore 150 x 20 x 10 mm | Valid model; 30,000 mm^3 | Passed after the invalid-input tests. |

See the [test summary](json_version/test_suite_5_cases/summary.md) for the case folders, logs, and validation records. Successful cases also include STEP/STL files and previews. The original 100 mm example and the earlier 150 mm test record were preserved.

## Next steps for the team

- **Robert:** try this example in your environment. We can agree on how your runner/API passes the dimensions and returns the generated file locations. The current prototype reads a sibling `dimensions.json` and writes to the same folder as the script.
- **Yinqi:** use the JSON fields and sample STL for the editable dimensions and preview workflow. We should agree on whether the UI needs STL or GLB and who handles conversion.
- **Xiyang:** help connect this template to the runner and UI, then start the next agreed CAD template, such as a plate with a hole.

The immediate team goal is to connect editable dimensions to the existing CAD generation and file download workflow.
