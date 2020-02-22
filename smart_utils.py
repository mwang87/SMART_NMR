

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
        if 'xls' in input_filename:
            qc = pd.read_excel(input_filename)
        else:
            # Cleaning non ascii data
            from tempfile import NamedTemporaryFile
            f = NamedTemporaryFile(delete=False)
            clean_input_filename = f.name
            with open(clean_input_filename, "wb") as clean_input:
                input_text = open(input_filename).read().encode('ascii', errors="ignore")
                clean_input.write(input_text)
            
            qc = pd.read_csv(clean_input_filename, sep=None) # Sniffing out delimiter

            os.unlink(clean_input_filename)
    except:
        pass

    # Seeing if we can parse it as topspin
    if not "1H" in qc:
        qc = topspin_to_pd(input_filename)

    
    
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


# Creating a canvas of structure images for projector
def draw_structures(structure_list, output_filename):
    import requests
    import urllib.parse

    local_folder_name = "temp"
    for i, structure in enumerate(structure_list):
        r = requests.get("https://gnps-structure.ucsd.edu/structureimg?smiles={}&width=300&height=300".format(urllib.parse.quote(structure)))
        output_filename = os.path.join(local_folder_name, "{0:03d}.png".format(i))
        

        print(output_filename)