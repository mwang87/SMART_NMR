import requests

def test_entry_test():
    url = "https://mingwangbeta.ucsd.edu/analyzeentryclassic"
    PARAMS = {'peaks': open("CDCl3_SwinholideA.csv").read()} 
    requests.post(url, params=PARAMS)

def test_entry_dev():
    url = "https://smart-dev.ucsd.edu/analyzeentryclassic"
    PARAMS = {'peaks': open("CDCl3_SwinholideA.csv").read()} 
    requests.post(url, params=PARAMS)