import sys
sys.path.insert(0, "..")
import smart_utils


def test_draw():
    smart_utils.draw_nmr("CDCl3_SwinholideA.csv", "CDCl3_SwinholideA.png")