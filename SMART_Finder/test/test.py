import sys
sys.path.insert(0, "..")
import SMART_FPinder
import glob
import os

DB, model, model_mw = SMART_FPinder.load_models(db_folder="..", models_folder="../models")

def test_csv():
    all_input_files = glob.glob(os.path.join("../input/*"))

    for input_filename in all_input_files:
        print(input_filename)

        SMART_FPinder.search_CSV(input_filename, \
            DB, model, model_mw, \
            "output_results.tsv", \
            "output_nmr.png", \
            "output_candidates.png", \
            mw=None)
