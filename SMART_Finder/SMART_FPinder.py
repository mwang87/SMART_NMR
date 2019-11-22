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
import sys

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
import json

import argparse

def load_models(models_folder="models"):
    #importing trained model
    #If no gpus are available, these models are working with CPU automatically
    with tf.device('/CPU:0'):
        model = keras.models.load_model(os.path.join(models_folder, 'HWK_sAug_1106_final(2048r1)_cos.hdf5'))
        model_mw = keras.models.load_model(os.path.join(models_folder, 'VGG16_high_aug_MW_continue.hdf5'))

    return model, model_mw

def load_db(db_folder="."):
    #loading DB
    DB = np.load(os.path.join(db_folder, 'FPinder_DB.npy'), allow_pickle=True)

    return DB

#This is a binary cosine between two sets
def cosine(x,y):
    '''x, y are same shape array'''
    a = set(x)
    b = set(y)
    return (len(a&b))/(sqrt(len(a))*sqrt(len(b)))


def draw_candidates(candidates_df, output_png, topk=10):#i is compound name used for file name. (ex abc.csv)
    smiles_input = candidates_df["SMILES"]
    names = []
    mols = []
    
    number_candidates = len(candidates_df)
    molsPerRow = 2
    if topk == 1:
        molsPerRow = 2
    elif topk < 5:
        molsPerRow = 3
    else:
        molsPerRow = 5
    for j in range(topk):
        try:
            smiles_candi = Chem.MolFromSmiles(neighbors.iat[j,1])        
            mols.append(smiles_candi)
            candi_name = neighbors.iat[j,0]+'({})'.format(neighbors.iat[j,2].round(2))
            names.append(candi_name)
        except:
            continue
    try:
        Draw.MolsToGridImage(mols, molsPerRow=molsPerRow, subImgSize=(300, 300),legends=names ,highlightAtomLists=None, highlightBondLists=None, useSVG=False).save(output_png)
    except:
        print("RDKIT error, see the csv file in result folder")
        raise

def CSV_converter(CSV_converter): # Converting CSV file to numpy array (200 x 240), # i = CSV file name
    try:
        qc = pd.read_csv(CSV_converter, sep=",")
        qc["1H"]
    except:
        qc = pd.read_csv(CSV_converter, sep="\t")
        qc["1H"]

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

def predict_nmr(input_nmr_filename, model, model_mw):
    mat = CSV_converter(input_nmr_filename)

    ### Model Prediction
    fingerprint_prediction = model.predict(mat.reshape(1,200,240,1))
    #TODO: Annotate Logic Here
    fingerprint_prediction_nonzero = np.where(fingerprint_prediction.round()[0]==1)[0] 
    pred_MW = model_mw.predict(mat.reshape(1,200,240,1)).round()[0][0] #Model to Preduct the molecular mass

    return fingerprint_prediction, fingerprint_prediction_nonzero, pred_MW
        
def search_CSV(input_nmr_filename, DB, model, model_mw, output_table, output_nmr_image, output_pred_fingerprint, mw=None, top_candidates=20): # i = CSV file name
    mat = CSV_converter(input_nmr_filename)

    # plotting and saving constructed HSQC images
    ## image without padding and margin
    height, width = mat.shape
    figsize = (10, 10*height/width) if height>=width else (width/height, 1)
    plt.figure(figsize=figsize)
    plt.imshow(mat, cmap=plt.cm.binary)
    plt.axis('off'), plt.xticks([]), plt.yticks([])
    plt.tight_layout()
    plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, hspace = 0, wspace = 0)
    plt.savefig(output_nmr_image, dpi=600)
    plt.close()

    fingerprint_prediction, fingerprint_prediction_nonzero, pred_MW = predict_nmr(input_nmr_filename, model, model_mw)
    
    #TODO: Annotate Logic Here
    # Database structure, 2 must be the predictions for the DB, 3, must be the mass
    topK = np.full((len(DB),4), np.nan, dtype=object)
    for j in range(len(DB)):
        try:
            real = DB[j][2]
            score = cosine(fingerprint_prediction_nonzero, real)
            if mw == None:
                if score > 0.7 and abs(DB[j][3]-pred_MW)/(DB[j][3]) < 0.1 :
                    topK[j] = DB[j][0], DB[j][1],score, DB[j][3]
            else:
                if score > 0.7 and abs(DB[j][3]-mw) < 20 :
                    topK[j] = DB[j][0], DB[j][1],score, DB[j][3]
        except:
            continue
    
    #Saving the DB Search
    topK = pd.DataFrame(topK, columns = ['Name','SMILES','Cosine score','MW'])
    topK = topK.dropna(how='all')
    topK = topK.sort_values(['Cosine score'], ascending = False)
    topK = topK.drop_duplicates(['SMILES'])
    topK = topK[:top_candidates]
    topK = topK.fillna('No_name') #Time
    topK.to_csv(output_table, index = None)

    #Saving the predicted Fingerprint
    open(output_pred_fingerprint, "w").write(json.dumps(fingerprint_prediction.tolist()))

    #TODO: Evaluate if we want to remove the code to not have the drawing
    #draw_candidates(topK, output_candidate_image)

def main():
    DB = load_db()
    model, model_mw = load_models()

    parser = argparse.ArgumentParser(description='SMART Embedding')
    parser.add_argument('input_csv', help='input_csv')
    parser.add_argument('output_table', help='output_table')
    parser.add_argument('output_nmr_image', help='output_nmr_image')
    parser.add_argument('output_pred_fingerprint', help='output_pred_fingerprint')
    parser.add_argument('--molecular_weight', default=None, type=float, help='molecular_weight')
    args = parser.parse_args()

    search_CSV(args.input_csv, DB, model, model_mw, args.output_table, args.output_nmr_image, args.output_pred_fingerprint, mw=args.molecular_weight)



if __name__ == "__main__":
    main()