"""Parametric rectangular bar; all dimensions are in millimeters.

Run with Python in an environment containing cadgen[snapshot]==0.7.10:
    python rectangular_bar.py

Both STEP and STL are regenerated beside this source file.
STL coordinates use millimeters (STL itself has no unit metadata).
"""

from cadgen import build123d as bd
from cadgen import step, stl

LENGTH_MM = 100.0
WIDTH_MM = 20.0
HEIGHT_MM = 10.0


@step(out="rectangular_bar.step")
@stl(out="rectangular_bar.stl")
def rectangular_bar():
    """One solid with its minimum X/Y/Z corner at the origin."""
    bar = bd.Box(
        LENGTH_MM,
        WIDTH_MM,
        HEIGHT_MM,
        align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN),
    )
    bar.label = "rectangular_bar_100x20x10_mm"
    return bar


if __name__ == "__main__":
    rectangular_bar()
