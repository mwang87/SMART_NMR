

import pandas as pd
import numpy as np
import csv
import os
import matplotlib.pyplot as plt

## Written by Joseph Egan
def topspin_to_pd(input_filename):
    ###row_dict was written by Jeff van Santen ###
    Rows = dict()
    with open(input_filename) as p:
        reader = csv.reader(p, delimiter=" ")
        for row in reader:
            row = [x for x in row if x]
            if "#" in row or not row:
                continue
            else:
                try:
                    Rows[row[0]] = [row[3],row[4]]
                except:
                    pass

    HSQC_Data_df = pd.DataFrame.from_dict(Rows, orient='index',columns = ['1H','13C']).astype('float')
    HSQC_Data_df = HSQC_Data_df.sort_values(by=['1H'],ascending = True).round({'1H':2,'13C':1})

    return HSQC_Data_df

def hsqc_to_np(input_filename,C_scale=100,H_scale=100, output_numpy=None): # x is csv filename ex) flavonoid.csv
      
    qc = pd.DataFrame()

    # First try to parse as standard csv/tsv files
    try:
        qc = pd.read_excel(input_filename)
       
    except:
        try:
            qc = pd.read_csv(input_filename, sep=None, encoding='utf-8-sig') # Sniffing out delimiter
        except:
            pass
        

    # Seeing if we can parse it as topspin
    if not "1H" in qc:
        qc = topspin_to_pd(clean_input_filename)

    os.unlink(clean_input_filename)
    
    qc = qc.dropna()
    H = (qc['1H']*H_scale//12).astype(int)
    C = (qc['13C']*C_scale//200).astype(int)
    mat = np.zeros((C_scale,H_scale), int)
    for j in range(len(qc)): # number of index of C and H is same
        a, b = H.iloc[j], C.iloc[j]
        if 0 <= a < H_scale and 0 <= b < C_scale:
            mat[b, H_scale-a-1] = 1

    if output_numpy is not None:
        np.save(output_numpy, mat)

    return mat

def draw_nmr(input_filename, output_png, dpi=300, display_name=None):
    mat = hsqc_to_np(input_filename)
    # getting scale
    C_scale, H_scale = mat.shape[0], mat.shape[1]
    # plotting and saving constructed HSQC images
    ## image without padding and margin
    plt.figure()
    ax = plt.axes()
    plt.imshow(mat, cmap=plt.cm.binary)
    ax.set_ylim(C_scale,0)
    ax.set_xlim(0,H_scale)
    plt.axis()
    plt.xticks(np.arange(H_scale+1,step=H_scale/12), (list(range(12,0-1,-1))))
    plt.yticks(np.arange(C_scale+1,step=C_scale/10), (list(range(0,200+1,20))))
    ax.set_xlabel('1H [ppm]')
    ax.set_ylabel('13C [ppm]')
    plt.grid(True,linewidth=0.5,alpha=0.5)
    plt.tight_layout()
    if display_name is None:
        plt.text(4, 6, input_filename, ha='left', wrap=True)
    else:
        plt.text(4, 6, display_name, ha='left', wrap=True)
    
    plt.savefig(output_png, dpi=dpi)
    plt.close()
