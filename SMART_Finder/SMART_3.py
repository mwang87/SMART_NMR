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

import matplotlib as mpl
import matplotlib.pyplot as plt
from math import sqrt
import time
import json

import argparse
scale = 128 

def load_models(models_folder="models"):
    #importing trained model
    #If no gpus are available, these models are working with CPU automatically
    with tf.device('/CPU:0'):
        model_1ch = keras.models.load_model(os.path.join(models_folder, '(011721)SMART3_v3_1ch_RC.hdf5'))
        model_2ch = keras.models.load_model(os.path.join(models_folder, '(011721)SMART3_v3_2ch_RC.hdf5'))
        model_1ch_class = keras.models.load_model(os.path.join(models_folder, '(011621)SMART3_v3_1ch_class_g.hdf5'))
        model_2ch_class = keras.models.load_model(os.path.join(models_folder, '(011621)SMART3_v3_2ch_class_g.hdf5'))
        #model_mw = keras.models.load_model(os.path.join(models_folder, 'VGG16_high_aug_MW_continue.hdf5'))

    return model_1ch, model_2ch, model_1ch_class, model_2ch_class 

def load_db(db_folder="."):
    #loading DB
    #DB = np.load(os.path.join(db_folder, 'FPinder_DB.npy'), allow_pickle=True)
    DB =np.array(pd.read_json('DB_010621_SM3.json'))
    with open('superclass.json','r') as r:
        index_super = json.load(r)
    return DB, index_super

#This is a binary cosine between two sets
def cosine(x,y):
    '''x, y are same shape array'''
    a = set(x)
    b = set(y)
    return (len(a&b))/(sqrt(len(a))*sqrt(len(b)))


def CSV_converter(CSV_converter, channel = 1): # Converting CSV file to numpy array (128 x 128), # i = CSV file name
    _, ext = os.path.splitext(CSV_converter)
    if ext in [".xls",".xlsx"]:
        qc = pd.read_excel(CSV_converter)
    elif ext == '.csv':
        qc = pd.read_csv(CSV_converter)
    elif ext == '.tsv':
        qc = pd.read_csv(CSV_converter, sep="\t")
    
    qc = qc.dropna()
    H = (qc['1H']*scale//12).astype(int)
    C = (qc['13C']*scale//240).astype(int)
    if channel == 2: # edited HSQC with intensity
        T = qc['Intensity']
        mat = np.zeros((scale,scale,2), float)
        for j in range(len(qc)): 
            a, b = H.iloc[j].astype(int), C.iloc[j].astype(int)
            t = T.iloc[j]
            if 0 <= a < scale and 0 <= b < scale and t > 0:# + phase
                mat[b, scale-a-1,0] = 1
            elif 0 <= a < scale and 0 <= b < scale and t < 0:# - phase
                mat[b, scale-a-1,1] = 1
    elif channel == 1:
        mat = np.zeros((scale,scale,1), float)
        for j in range(len(qc)): 
            a, b = H.iloc[j].astype(int), C.iloc[j].astype(int)
            if 0 <= a < scale and 0 <= b < scale:
                mat[b, scale-a-1,0] = 1
    return mat

def predict_nmr(input_nmr_filename, channel, model, model_class):
    mat = CSV_converter(input_nmr_filename, channel)

    ### Model Prediction
    fingerprint_prediction, pred_MW  = model.predict(mat.reshape(1,scale,scale,channel))
    fingerprint_prediction = fingerprint_prediction[0].round()
    pred_MW = pred_MW[0][0]
    #TODO: Annotate Logic Here
    fingerprint_prediction = np.where(fingerprint_prediction == 1)[0] 
    pred_class = np.argmax(model_class.predict(mat.reshape(1,scale,scale,channel))[0],-1)
    return fingerprint_prediction, pred_MW, pred_class #array, array, array

def search_database(fingerprint_prediction, pred_MW, DB, mw=None, top_candidates=20):
    #TODO: Annotate Logic Here
    # Database structure, 2 must be the predictions for the DB, 3, must be the mass
    #topK = np.full((len(DB),4), np.nan, dtype=object)
    results_list = []
    DB_len = len(DB)
    topK = np.full((DB_len,4), np.nan, dtype=object)
    for j in range(DB_len):
        if mw == None: #If we don't provide a user input mw, we should use the prediction
            DB_mw = DB[j][3]
            if abs(DB_mw-pred_MW)/(DB_mw) < 0.2 :
                DB_fp = DB[j][1]
                score = cosine(fingerprint_prediction,DB_fp)
                if score > 0.6:
                    topK[j] = DB[j][0], DB[j][2], score, DB_mw
        
        else:
            real_mw = DB[j][3]
            if abs(real_mw-pred_mw) <20:
                DB_fp = DB[j][1]
                score = cosine(fingerprint_prediction,DB_fp)
                if score > 0.6:
                    topK[j] = DB[j][0], DB[j][2], score, DB_mw
            

    
    #Saving the DB Search
    topK = pd.DataFrame(topK, columns = ['Name','SMILES','Cosine score','MW'] )
    topK = topK.dropna(how='all')
    topK = topK.sort_values(['Cosine score'], ascending = False)
    topK = topK.drop_duplicates(['SMILES'])
    topK = topK[:top_candidates]
    topK = topK.fillna('No_name') #Time

    return topK

def search_CSV(input_nmr_filename, DB, model, model_class, channel, output_table, output_nmr_image, output_pred_fingerprint, mw=None, top_candidates=20): # i = CSV file name
    mat = CSV_converter(input_nmr_filename)

    # plotting and saving constructed HSQC images
    ## image without padding and margin
    height, width = scale, scale
    figsize = (10, 10)
    plt.figure(figsize=figsize)
    ax = plt.axes()
    try:
        plt.imshow(mat[:,:,1], mpl.colors.ListedColormap([(0.2, 0.4, 0.6, 0),'blue']))
        plt.imshow(mat[:,:,0], mpl.colors.ListedColormap([(0.2, 0.4, 0.6, 0),'red']))
    except:
        plt.imshow(mat[:,:,0], mpl.colors.ListedColormap([(0.2, 0.4, 0.6, 0),'red']))
    ax.set_ylim(scale-1,0)
    ax.set_xlim(0,scale-1)
    
    plt.axis()
    plt.xticks(np.arange(scale+1,step=scale/12), (list(range(12,0-1,-1))))
    plt.yticks(np.arange(scale+1,step=scale/12), (list(range(0,240+1,20))))
    ax.set_xlabel('1H [ppm]')
    ax.set_ylabel('13C [ppm]')
    plt.grid(True,linewidth=0.5, alpha=0.5)
    plt.tight_layout()
    #plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, hspace = 0, wspace = 0)
    plt.savefig(output_nmr_image, dpi=600)
    plt.close()

    fingerprint_prediction, pred_MW, pred_class = predict_nmr(input_nmr_filename, channel, model, model_class)
    
    topK = search_database(fingerprint_prediction, pred_MW, DB, mw=mw, top_candidates=top_candidates)

    #Saving TopK
    topK.to_csv(output_table, index = None)
    
    #Saving the predicted Fingerprint
    open(output_pred_fingerprint, "w").write(json.dumps(fingerprint_prediction.tolist()))

    #TODO: Evaluate if we want to remove the code to not have the drawing
    #draw_candidates(topK, output_candidate_image)

def main():
    DB, index_super = load_db()
    model_1ch, model_2ch, model_1ch_class, model_2ch_class = load_models()

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
