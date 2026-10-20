"""Build and verify a rectangular bar from the sibling dimensions.json.

Requires cadgen==0.7.10. Run this file again after editing only dimensions.json.
STEP, STL and rectangular_bar_validation.json are written beside this script.
All paths are anchored to this file, so the working directory does not matter.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "dimensions.json"
REPORT = HERE / "rectangular_bar_validation.json"


class ConfigurationError(ValueError):
    """A missing, malformed, or unsupported model parameter."""


def load_dimensions() -> dict:
    """Read and validate configuration; this read is also tracked inside a build."""
    try:
        raw = CONFIG.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ConfigurationError(f"\u627e\u4e0d\u5230\u914d\u7f6e\u6587\u4ef6\uff1a{CONFIG}") from exc
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(f"\u65e0\u6cd5\u8bfb\u53d6 dimensions.json\uff1a{exc}") from exc
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"dimensions.json \u4e0d\u662f\u6709\u6548 JSON\uff08\u7b2c {exc.lineno} \u884c\uff0c\u7b2c {exc.colno} \u5217\uff09\uff1a{exc.msg}"
        ) from exc
    if not isinstance(values, dict):
        raise ConfigurationError("dimensions.json \u7684\u6700\u5916\u5c42\u5fc5\u987b\u662f JSON \u5bf9\u8c61\u3002")
    missing = [key for key in ("units", "length", "width", "height") if key not in values]
    if missing:
        raise ConfigurationError(f"dimensions.json \u7f3a\u5c11\u5fc5\u586b\u5b57\u6bb5\uff1a{', '.join(missing)}\u3002")
    if values["units"] != "mm":
        raise ConfigurationError('units \u5fc5\u987b\u4e3a "mm"\uff1b\u6b64\u7248\u672c\u4f7f\u7528\u6beb\u7c73\u3002')
    dimensions = {"units": "mm"}
    for key in ("length", "width", "height"):
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigurationError(f"{key} \u5fc5\u987b\u662f\u5927\u4e8e 0 \u7684\u6709\u9650\u6570\u5b57\uff0c\u5f53\u524d\u503c\u4e3a {value!r}\u3002")
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise ConfigurationError(f"{key} \u5fc5\u987b\u662f\u5927\u4e8e 0 \u7684\u6709\u9650\u6570\u5b57\u3002") from exc
        if not math.isfinite(number) or number <= 0:
            raise ConfigurationError(f"{key} \u5fc5\u987b\u662f\u5927\u4e8e 0 \u7684\u6709\u9650\u6570\u5b57\uff0c\u5f53\u524d\u503c\u4e3a {value!r}\u3002")
        dimensions[key] = number
    return dimensions


# The cadgen re-export is lazy: importing this file does not load the CAD kernel.
from cadgen import build123d as bd
from cadgen import step, stl


@step(out="rectangular_bar.step")
@stl(out="rectangular_bar.stl")
def rectangular_bar():
    # Read INSIDE the model so cadgen tracks JSON edits as build dependencies.
    dimensions = load_dimensions()
    bar = bd.Box(
        dimensions["length"],
        dimensions["width"],
        dimensions["height"],
        align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN),
    )
    bar.label = "rectangular_bar_json"
    return bar


def write_report(report: dict) -> None:
    """Replace the report atomically, including failed-run reports."""
    temporary = REPORT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(REPORT)


def main() -> int:
    # Use UTF-8 for Chinese diagnostics in Windows terminals and redirected logs.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    # A direct build avoids this installation's background service startup issue.
    os.environ.setdefault("CADGEN_DAEMON", "0")
    stage = "configuration"
    dimensions = None
    input_sha256 = None
    try:
        dimensions = load_dimensions()  # Fail clearly before starting a build.
        input_sha256 = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
        stage = "generation"
        rectangular_bar()
        if hashlib.sha256(CONFIG.read_bytes()).hexdigest() != input_sha256:
            raise RuntimeError("\u751f\u6210\u671f\u95f4 dimensions.json \u88ab\u4fee\u6539\uff1b\u8bf7\u91cd\u65b0\u8fd0\u884c\u540c\u4e00\u811a\u672c\u3002")
        stage = "validation"
        from validate_geometry import validate_outputs

        report = validate_outputs(HERE, dimensions)
        report.update({
            "configuration_file": CONFIG.name,
            "configuration_sha256": input_sha256,
            "input_dimensions": dimensions,
            "stage": "complete" if report["passed"] else "validation",
            "artifacts_updated": True,
            "artifacts_sha256": {
                name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                for name in ("rectangular_bar.step", "rectangular_bar.stl")
            },
        })
        write_report(report)
        if not report["passed"]:
            print(f"\u9a8c\u8bc1\u5931\u8d25\uff1a\u8bf7\u67e5\u770b {REPORT}", file=sys.stderr)
            return 1
    except (Exception, SystemExit) as exc:
        error = (
            f"CAD \u5bfc\u51fa\u9000\u51fa\u7801 {exc.code}\uff1b\u8be6\u89c1\u4e0a\u65b9 CAD \u9519\u8bef\u8f93\u51fa\u3002"
            if isinstance(exc, SystemExit)
            else str(exc) or type(exc).__name__
        )
        failure = {
            "passed": False,
            "stage": stage,
            "configuration_file": CONFIG.name,
            "configuration_sha256": input_sha256,
            "input_dimensions": dimensions,
            "error": error,
            "artifacts_updated": False,
            "note": "\u672c\u6b21\u8fd0\u884c\u672a\u5b8c\u6210\uff1b\u5df2\u6709 STEP/STL \u4e0d\u80fd\u89c6\u4e3a\u5f53\u524d\u914d\u7f6e\u7684\u6709\u6548\u7ed3\u679c\u3002",
        }
        write_report(failure)
        label = "\u914d\u7f6e\u9519\u8bef" if stage == "configuration" else "\u751f\u6210\u6216\u9a8c\u8bc1\u9519\u8bef"
        print(f"{label}\uff1a{error}", file=sys.stderr)
        return 2 if stage == "configuration" else 1
    print(
        f"\u9a8c\u8bc1\u901a\u8fc7\uff1a{dimensions['length']:g} \xd7 {dimensions['width']:g} \xd7 "
        f"{dimensions['height']:g} mm\uff1bSTEP\u3001STL \u548c\u9a8c\u8bc1\u62a5\u544a\u5df2\u66f4\u65b0\u81f3 {HERE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
