# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 09:28:19 2022

@author: Ben
"""

import numpy as np
import matplotlib.pyplot as plt

def sliceViewer(volume, zStackStep, colMap):
    print('Use X to move down, and Z to move up through the stack')
    fig, ax = plt.subplots()
    ax.volume = volume
    ax.index = 0
    ax.imshow(volume[ax.index], cmap = colMap)
    fig.canvas.mpl_connect('key_press_event', process_key)
    plt.axis('off')
    depth = int(ax.index)
    textstr = 'Depth = ' + format(depth, '03d') + 'um'
    props = dict(boxstyle='round', facecolor='wheat', alpha=1.0)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', bbox=props)
    global z
    z=zStackStep 
    

def process_key(event):
    fig = event.canvas.figure
    ax = fig.axes[0]
    if event.key == 'z':
        previous_slice(ax, z)
    elif event.key == 'x':
        next_slice(ax)
    fig.canvas.draw()

def previous_slice(ax, z):
    volume = ax.volume
    ax.index = (ax.index - 1) % volume.shape[0]  # wrap around using %
    ax.images[0].set_array(volume[ax.index])
    
    depth = int(ax.index * z * 0.1)
    textstr = 'Depth = ' + format(depth, '03d') + 'um'
    props = dict(boxstyle='round', facecolor='wheat', alpha=1.0)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', bbox=props)

def next_slice(ax):
    volume = ax.volume
    ax.index = (ax.index + 1) % volume.shape[0]
    ax.images[0].set_array(volume[ax.index])
    
    depth = int(ax.index * z * 0.1)
    textstr = 'Depth = ' + format(depth, '03d') + 'um'
    props = dict(boxstyle='round', facecolor='wheat', alpha=1.0)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', bbox=props)