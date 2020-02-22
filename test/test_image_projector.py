import pandas as pd
import requests
import urllib.parse
import sys
sys.path.insert(0, "..")
import smart_utils

def test():
    df = pd.read_csv("Result_Data/resultclassictable.csv")
    records = df.to_dict(orient="records")
    smiles_list = [entry["SMILES"] for entry in records]
    smart_utils.draw_structures(smiles_list, "merged_structures.png")