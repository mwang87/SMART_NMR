#################################################################
##                         SMART_FPinder                      ###
##                Extremely experimental version              ###
##   Developed by Hyunwoo Kim, Chen Zhang, and Raphael Reher  ###
##         William H. Gerwich and Garrison W. Cottrell        ###
##                        October, 2019                       ###
#################################################################


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import datasets, layers, models

import numpy as np
import pandas as pd
import datetime
import os

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem import Draw
#from rdkit.Chem.Draw import IPythonConsole
from rdkit.Chem import Descriptors
from rdkit.Chem import AllChem
from rdkit import DataStructs

import matplotlib.pyplot as plt
from math import sqrt
import time

#importing trained model
#If no gpus are available, these models are working with CPU automatically
with tf.device('/CPU:0'):
    model = keras.models.load_model('models/HWK_sAug_1106_final(2048r1)_cos.hdf5')
    model_mw = keras.models.load_model('models/VGG16_high_aug_MW_continue.hdf5')
#loading DB
DB = np.load('FPinder_DB.npy')

def cosine(x,y):
    '''x, y are same shape array'''
    a = set(x)
    b = set(y)
    return (len(a&b))/(sqrt(len(a))*sqrt(len(b)))


def drawing(i,n):#i is compound name used for file name. (ex abc.csv)
    neighbors = pd.read_csv('Result/{}'.format(i))
    smiles_input = neighbors.columns[1]
    names = []
    mols = []
    
    if n == 1:
        molsPerRow = 2
    elif n == 5:
        molsPerRow = 3
    elif n == 10:
        molsPerRow = 5
    for j in range(n):
        try:
            smiles_candi = Chem.MolFromSmiles(neighbors.iat[j,1])        
            mols.append(smiles_candi)
            candi_name = neighbors.iat[j,0]+'({})'.format(neighbors.iat[j,2].round(2))
            names.append(candi_name)
        except:
            continue
    try:
        Draw.MolsToGridImage(mols, molsPerRow=molsPerRow, subImgSize=(300, 300),legends=names ,highlightAtomLists=None, highlightBondLists=None, useSVG=False).save('Result/{}.png'.format(i[:-4]))
    except:
        print("RDKIT error, see the csv file in result folder")

def CSV_converter(i): # Converting CSV file to numpy array (200 x 240), # i = CSV file name
    qc = pd.read_csv('input/{}'.format(i))
    qc = qc.dropna()
    H = (qc['1H']*240//12).astype(int)
    C = (qc['13C']*200//200).astype(int)
    try: #Considering peak intensities
        INT = qc['Intensity']
        mat = np.zeros((200,240), float)
        for j in range(len(qc)): 
            a, b = H.iloc[j].astype(int), C.iloc[j].astype(int)
            if 0 <= a <= 239 and 0 <= b <= 199:
                if mat[b, 239-a] < abs(INT[j]):
                    mat[b, 239-a] = abs(INT[j])
        mat = mat/mat.max()
    except: # if intensities are not provided
        mat = np.zeros((200,240), float)
        for j in range(len(qc)): 
            a, b = H.iloc[j].astype(int), C.iloc[j].astype(int)
            if 0 <= a < 240 and 0 <= b < 200:
                mat[b, 239-a] = 1
    return mat
        
def search_CSV(i, mw=None): # i = CSV file name
    mat = CSV_converter(i)
    # plotting and saving constructed HSQC images
    ## image without padding and margin
    height, width = mat.shape
    figsize = (10, 10*height/width) if height>=width else (width/height, 1)
    plt.figure(figsize=figsize) 
    plt.imshow(mat, cmap=plt.cm.binary)
    plt.axis('off'), plt.xticks([]), plt.yticks([])
    plt.tight_layout()
    plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, hspace = 0, wspace = 0)
    plt.savefig('Result/{}_HSQC.png'.format(i[:-4]),dpi=600)
    
    pred = np.where(model.predict(mat.reshape(1,200,240,1)).round()[0]==1)[0]
    pred_MW = model_mw.predict(mat.reshape(1,200,240,1)).round()[0][0]
    plt.close()
    
    topK = np.full((len(DB),4), np.nan, dtype=object)
    for j in range(len(DB)):
        try:
            real = DB[j][2]
            score = cosine(pred,real)
            if mw == None:
                if score > 0.7 and abs(DB[j][3]-pred_MW)/(DB[j][3]) < 0.1 :
                    topK[j] = DB[j][0], DB[j][1],score, DB[j][3]
            else:
                if score > 0.7 and abs(DB[j][3]-mw) < 20 :
                    topK[j] = DB[j][0], DB[j][1],score, DB[j][3]
                
        except:
            continue
    
    topK = pd.DataFrame(topK, columns = ['Name','SMILES','Cosine score','MW'])
    topK = topK.dropna(how='all')
    topK = topK.sort_values(['Cosine score'], ascending = False)
    topK = topK.drop_duplicates(['SMILES'])
    topK = topK[:20]
    topK = topK.fillna('No_name') #Time
    topK.to_csv('Result/{}'.format(i), index = None)
    return drawing(i,10)


i = str(input("Input file name? (ex gerwick.csv):"))

if i not in os.listdir("input/"):
    i = str(input("Input file name? (ex gerwick.csv):"))
    print("No file in input folder")
        
mwQ = input("Do you know the molecular weight?(y/n):")
if mwQ == 'Y' or mwQ == 'y' or mwQ == 'yes' or mwQ == 'Yes' or mwQ=='YES':
    mw = float(input("please enter the molecular weight:"))
else:
    mw = None

print("now searching...")
search_CSV(i,mw)
print("Done")
