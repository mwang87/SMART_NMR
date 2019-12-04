

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def hsqc_to_np(input_filename, output_numpy=None): # x is csv filename ex) flavonoid.csv
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

    if output_numpy is not None:
        np.save(output_numpy, mat)

    return mat

def draw_nmr(input_filename, output_png):
    mat = hsqc_to_np(input_filename)

    # plotting and saving constructed HSQC images
    ## image without padding and margin
    height, width = mat.shape
    figsize = (10, 10*height/width) if height>=width else (width/height, 1)
    plt.figure(figsize=figsize)
    plt.imshow(mat, cmap=plt.cm.binary)
    plt.axis('off'), plt.xticks([]), plt.yticks([])
    plt.tight_layout()
    plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, hspace = 0, wspace = 0)
    plt.savefig(output_png, dpi=600)
    plt.close()