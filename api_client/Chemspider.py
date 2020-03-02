from bs4 import BeautifulSoup
from urllib.request import urlopen
import time
from tqdm import tqdm
import numpy as np
import pandas as pd

def Find_ChemSP(Name): #Compound Name
    Name = Name.replace(' ','%20') #removing space from compound name
    delay = np.random.randint(1,4) # for avoiding blocking 
    time.sleep(delay)
    url = f"https://www.chemspider.com/Search.aspx?q={Name}" #seraching URL
    result = urlopen(url)
    html = result.read()
    soup = BeautifulSoup(html, 'html.parser')
    smiles = soup.select('span[id=ctl00_ctl00_ContentSection_ContentPlaceHolder1_RecordViewDetails_rptDetailsView_ctl00_moreDetails_WrapControl2]')
    
    return smiles
