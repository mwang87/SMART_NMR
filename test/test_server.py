import requests

def test_entry():
    url = "https://mingwangbeta.ucsd.edu/analyzeentryclassic"
    PARAMS = {'peaks': open("CDCl3_SwinholideA.csv").read()} 
    requests.post(url, params=PARAMS)