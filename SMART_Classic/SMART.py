#################################################################
##                         SMART_Alpha                        ###
##                Extremely experimental version              ###
## Developed by Henry (from Gary) and Three of SIO's postdocs ###
#################################################################

print("Warining : This version is Extremely experimental version")
print("loading packages....")
### data package ###
import pandas as pd
import numpy as np

### drawing package ###
import matplotlib as mpl 
import matplotlib.pyplot as plt # 그래프를 그리는 모듈
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Draw

###system package###
from math import sqrt
from tqdm import tqdm
import os
import subprocess

###Multiprocessing###
import multiprocessing
from multiprocessing import Pool
import argparse

### PATH of initial point
PATH = os.getcwd().replace('\\','/')

print("loading functions...")
### CSV to NPY###
def HSQCtoNPY(input_filename, output_numpy): # x is csv filename ex) flavonoid.csv
    qc = pd.read_csv(input_filename)
    qc = qc.dropna()
    scale = 100 #n by n
    H = (qc['1H']*scale//12).astype(int)
    C = (qc['13C']*scale//200).astype(int)
    mat = np.zeros((scale,scale), int)
    for j in range(len(qc)): #인덱스 수가 같으므로
        a, b = H.iloc[j], C.iloc[j]
        if 0 <= a < scale and 0 <= b < scale:
            mat[b, scale-a-1] = 1
    fig = plt.figure(figsize=(5.12,5.12)) #그림사이즈 300 x 300
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
    ax.imshow(mat, cmap=plt.cm.binary, interpolation=None)
    plt.xticks([], [])
    plt.yticks([], [])
    #plt.savefig('{}/convert/{}.png'.format(PATH,(x[:-4].replace(" ","_"))))
    np.save(output_numpy, mat)
    plt.clf()

### mesurement of cosine score ###
def cosine(x,y):
    '''x, y are same shape array'''
    return (np.sum(x*y)/(sqrt(np.sum(x**2))*sqrt(np.sum(y**2))))

### find top20 neighbors
def find_neighbors(x): #find neighbors from training set(20K)
    #1st step: extracting embeddings from output file
    out = np.load('{}/convert/{}'.format(PATH, x))
    training_embd = np.load('{}/lib/lib.npy'.format(PATH))
    #test_embd = np.load('{}/embedd_lib/test_embd.npy'.format(Dir))>> out_embed
    training_range = range(len(training_embd))
    out_embed = out[0][0]
    #2st step finding candidate from Jeol_20K dataset!
    rank = np.zeros((len(training_embd),3), dtype=object)
    for j in training_range:
        score = cosine(out_embed,training_embd[j][1])
        rank[j] = [training_embd[j][0], score, training_embd[j][2]]
    rank = pd.DataFrame(rank, columns = ['Name','Score','SMILES'])
    rank = rank.sort_values(by=['Score'], axis=0, ascending=False)
    rank = rank[:20]
    rank.to_csv('{}/convert/{}_Top20.csv'.format(PATH,x[:-4]), index=None)
    
    
### drawing TOP 8 neighbors ###
def drawing(x):#i is compound name used for file name.
    neighbors = pd.read_csv('{}/convert/{}'.format(PATH, x))
    smiles_input = neighbors.columns[2]
    names = []
    mol = Chem.MolFromSmiles(smiles_input)
    mols = []
    for j in range(9):
        smiles_candi = Chem.MolFromSmiles(neighbors.iat[j,2])
        candi_names = '{} ({})'.format(neighbors['Name'][j],round(neighbors['Score'][j],2))               
        mols.append(smiles_candi)
        names.append(candi_names)
    Draw.MolsToGridImage(mols,3,(300,300),legends = names).save('{}/result/{}9.png'.format(PATH,x[:-6]))


def main():
    parser = argparse.ArgumentParser(description='SMART Embedding')
    parser.add_argument('input_csv', help='input_csv')
    parser.add_argument('output_npy', help='output_npy')
    args = parser.parse_args()

    HSQCtoNPY(args.input_csv, args.output_npy)


if __name__ == "__main__":
    main()


# for i in tqdm(input_csv):
#     HSQCtoNPY(i)
#     a = subprocess.getoutput('docker run -v "{}/convert:/src/out" calclavia/smart:cli out/{}.npy out/{}.npy'.format(PATH,i[:-4].replace(" ","_"),i[:-4].replace(" ","_")))
#     print(a)
#     find_neighbors('{}.npy'.format(i[:-4].replace(" ","_")))
#     drawing('{}_Top20.csv'.format(i[:-4].replace(" ","_")))


