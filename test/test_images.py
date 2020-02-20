import sys
sys.path.insert(0, "..")
import smart_utils

def test_draw():
    smart_utils.draw_nmr("Data/CDCl3_SwinholideA.csv", "CDCl3_SwinholideA.png")
    smart_utils.draw_nmr("Data/cyclomarin_A_duggan2_input.csv", "x.png")
    smart_utils.draw_nmr("Data/cyclomarin_A_duggan_tsv.txt", "x.png")
    smart_utils.draw_nmr("Data/cyclomarin_A_fenical_tsv.txt", "x.png")
    smart_utils.draw_nmr("Data/cyclomarin_A_fenical_semicolon.csv", "x.png")