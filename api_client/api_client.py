import requests
import sys
import pandas as pd
import json

SERVER_URL = "http://localhost:6213"

input_csv_filename = sys.argv[1]

df = pd.read_csv(input_csv_filename, sep=",")
peaks_json = df.to_dict(orient="records")
r = requests.post(f"{SERVER_URL}/api/classic/embed", data={"peaks":json.dumps(peaks_json)})
r.raise_for_status()
print(peaks_json)
print(r.json())