import requests


def test_result():
    url = "https://smart-dev.ucsd.edu/result?task=81026499-aa2e-4bc0-bf6b-797d6f2e128e"
    r = requests.get(url)
    r.raise_for_status()