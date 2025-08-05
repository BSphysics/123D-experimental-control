# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 15:41:19 2024

@author: bs426
"""

import os
scriptDir = os.getcwd()
import sys
# import re
sys.path.append(os.path.join(scriptDir,"image viewer functions" ))
sys.path.append(os.path.join('D:\123D scripts\new PSHG script\new PSHG functions'))
import matplotlib.pyplot as plt
import numpy as np
from skimage import io

data_path = 'C:/Users/bs426/OneDrive - University of Exeter/!Work/Work.2024/Lab.2024/123D/2024_09_13 CST bead imaging/CST bead z stacks/Stack4 31_slices 1um_zStep'

files = os.listdir(data_path)
files_tiff = [i for i in files if i.endswith('.tif')]

for idx1 in range(len(files_tiff)):
    plt.close('all')
    filename = os.fsdecode(files_tiff[idx1])
    filename = r'/' + filename  
    imgs = io.imread(data_path + filename)
    
tpf = imgs[:, 1, :, :]
tpf[tpf<0] = 0

# plt.figure(1)
# plt.imshow(tpf[5,250:500,200:450])

s = np.sum(tpf[:, 250:500, 200:450],(1,2))
s=s-s[0]
s=s/np.max(s)

plt.figure(2)
plt.plot(s, ':ro')
plt.xlabel('z distance (um)')
plt.ylabel('Norm Intensity (A.U.)')
#%%

from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np


# https://stackoverflow.com/questions/18088918/combining-two-gaussians-into-another-guassian
def gauss(x, p): # p[0]==mean, p[1]==stdev, p[2]==height, p[3]==baseline                   
    a = p[2]
    mu = p[0]
    sig = p[1]
    #base = p[3]
    return a * np.exp(-1.0 * ((x - mu)**2.0) / (2.0 * sig**2.0)) #+ base

p0 = [2, 0.5, 1] # Inital guess is a normal distribution
p02 = [2, 2.7, 1]


z = np.linspace(-12, 16, 1000)
dz = z[1]-z[0]
convolved = np.convolve(gauss(z, p0),gauss(z, p02), mode="same")*dz
convolved=convolved/np.max(convolved)

zFrame=np.arange(-16,15)

plt.subplot(2, 1, 1)
plt.plot(zFrame, s,':ro')
plt.plot(z, convolved, lw=3, alpha=0.5,label="Convolved")
plt.xlim([-10, 10])
plt.xlabel('z distance (um)')
plt.ylabel('Norm Intensity (A.U.)')


plt.subplot(2, 1, 2)
plt.plot(z, gauss(z, p0), lw=3, alpha=0.5)
plt.plot(z, gauss(z, p02), lw=3, alpha=0.5)
plt.plot(z, convolved, lw=3, alpha=0.5,label="Convolved")
plt.legend()
plt.xlim([-10, 10])

plt.tight_layout()
plt.show()