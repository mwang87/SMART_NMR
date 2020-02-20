

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def hsqc_to_np(input_filename,C_scale=100,H_scale=100, output_numpy=None): # x is csv filename ex) flavonoid.csv
    qc = pd.read_csv(input_filename, sep=None) # Sniffing out delimiter
        
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
