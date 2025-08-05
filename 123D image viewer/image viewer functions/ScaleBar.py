# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 12:10:19 2022

@author: Ben
"""


import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Note - calibration data can be found in the following directories
# r'C:\Users\Ben\OneDrive - University of Exeter\!Work\Work.2020\Data\2020_03_16 FOV calib 25X\ZF3pt0\lateral\TPEF pngs'
# 50 micron step = 75 pixels (for Zf of 3pt0)

def ScaleBar(im, zoomFactor, scaleBarinMicrons, colour, full_filename):
    
    def micronsPerPixel(zoomFactor):
        mpp = 1.9634*zoomFactor**(-0.987)
        return mpp

    mpp = micronsPerPixel(zoomFactor)
    
    scaleBarLength = scaleBarinMicrons / mpp
    
    scaleBarWidth = 15

    scaleBar = patches.Rectangle((250, 475), scaleBarLength, scaleBarWidth, linewidth = 1, edgecolor = 'w', facecolor = colour)
    fig, ax = plt.subplots()
    ax.imshow(im, cmap = 'gray')
    ax.add_patch(scaleBar)
    plt.axis('off')
    plt.title('Scale bar = ' + str(scaleBarinMicrons) + r' $\mu$m', fontsize = 10)
    plt.savefig(full_filename, bbox_inches='tight', dpi = 1200)
    