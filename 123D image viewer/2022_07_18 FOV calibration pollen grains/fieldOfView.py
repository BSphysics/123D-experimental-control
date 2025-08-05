# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 11:39:32 2022

@author: Ben
"""

# TO DO: acquire bead data at lots of different zoom factors. plot relationship between zoomfactor and pixel size - should be able to 
# fit a function (some polynomial to this) which can be used in the future (or just hard code a look up table of values) 
# Once we have a value for pixel size in microns for each zoom factor, add something in tif2tiff123D that adds scale bars to each image.  

import os
scriptDir = os.getcwd()
import sys
sys.path.append(r'C:\Users\Ben\OneDrive - University of Exeter\!Work\Work.2022\Software\!functions')
sys.path.append(r'C:\Users\Ben\OneDrive - University of Exeter\!Work\Work.2022\Software\Lab scripts\General PSHG\new PSHG functions')
from tiff_loader import tiff_loader
import numpy as np
import matplotlib.pyplot as plt
from regionSelector import region_selector
from skimage.feature import match_template
from tkinter import ttk
from tkinter import filedialog
from tkinter.filedialog import askopenfilename
plt.close('all')

# data_path = r'C:\Users\Ben\OneDrive - University of Exeter\!Work\Work.2020\Data\2020_03_16 FOV calib 25X\ZF5pt0\lateral'
data_path = filedialog.askdirectory(initialdir = r'C:\Users\Ben\OneDrive - University of Exeter\!Work\Work.2022\Data\123D\2022_07_18 FOV calibration pollen grains')
[filenames, imgs] = [[],[]]
filenames, imgs = tiff_loader(data_path)
from imageMetaData import imageMetaData
zoom = imageMetaData(data_path, filenames)
zoom = int("".join(filter(str.isdigit, zoom)))

#%%
image1 = imgs[0,1,1,:,:]
image2 = imgs[1,1,1,:,:]

coords = region_selector(image1, 0, np.max(image1), 'Select region')
template = image1[int(coords[2]):int(coords[3]) , int(coords[0]):int(coords[1])]

result = match_template(image2, template)
ij = np.unravel_index(np.argmax(result), result.shape)
x, y = ij[::-1]

fig = plt.figure(figsize=(8, 3))
ax1 = plt.subplot(1, 2, 1)
ax2 = plt.subplot(1, 2, 2)
# ax3 = plt.subplot(1, 3, 3, sharex=ax2, sharey=ax2)

ax1.imshow(template, cmap=plt.cm.gray)
ax1.set_axis_off()
ax1.set_title('template')

ax2.imshow(image2, cmap=plt.cm.gray)
ax2.set_axis_off()
ax2.set_title('image')
hcoin, wcoin = template.shape
rect = plt.Rectangle((x, y), wcoin, hcoin, edgecolor='r', facecolor='none')
ax2.add_patch(rect)

pixelShiftX = np.abs(coords[0] - x)
pixelShiftY = np.abs(coords[2] - y)

print('\n Pixel shift along X = ' + str(pixelShiftX))
print('\n Pixel shift along y = ' + str(pixelShiftY))

pixelShift = np.round(np.sqrt(pixelShiftX**2 + pixelShiftY**2),1)
print('\n Total pixel shift = ' + str(pixelShift))




