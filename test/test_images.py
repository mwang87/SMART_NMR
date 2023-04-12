import sys
sys.path.insert(0, "..")
import smart_utils
import os
import glob

def test_draw():
    test_files = glob.glob("Data/*")

    for test_file in test_files:
        print(test_file)
        smart_utils.draw_nmr(test_file, "{}.png".format(os.path.basename(test_file)))