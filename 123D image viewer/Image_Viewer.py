# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 14:19:32 2020

@author: Ben
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
defaultDir = scriptDir + '\\Test data'
initialDir = r'D:\!User files'

from image_viewer_GUI import imageViewerGUI
[data_path, addScaleBar, empty, scaleBarSize, shg_path, shg_png_path,tpf_path,tpf_png_path, zstackPath, shg_png_zstackPath,tpf_png_zstackPath] = imageViewerGUI(initialDir,defaultDir)
scaleBarSize = float(scaleBarSize)
files = os.listdir(data_path)
files_tiff = [i for i in files if i.endswith('.tif')]

from imageMetaData import imageMetaData
zoomFactor , frames, zStackStep, allMetaData = imageMetaData(data_path, files_tiff)

from ScaleBar import ScaleBar

# %% 
    
for idx1 in range(len(files_tiff)):
    plt.close('all')
    filename = os.fsdecode(files_tiff[idx1])
    filename = r'/' + filename  
    imgs = io.imread(data_path + filename)
    
    if imgs.shape[0] == 0:
        continue

    numberOfImages = imgs.shape[0]
    
    if len(imgs.shape) == 3:
        print('\n pSHG images' + '\n')
        shg = imgs[0,:,:]
        tpf = imgs[1,:,:]
               
        if addScaleBar == True:
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_SHG_SCALE_BAR.tiff'
            full_filename =  shg_path / filename    
            ScaleBar(shg, zoomFactor, scaleBarSize, 'r', full_filename)
        else:
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_SHG.tiff'
            full_filename =  shg_path / filename 
            io.imsave(full_filename, shg)
        
            
        if addScaleBar == True:
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_TPEF_SCALE_BAR.tiff'
            full_filename =  tpf_path / filename    
            ScaleBar(tpf, zoomFactor, scaleBarSize, 'r', full_filename)
        else:
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_TPEF.tiff'
            full_filename =  tpf_path / filename 
            io.imsave(full_filename, tpf)
        
        shg_norm = shg / np.max(shg)
        shg_norm *= 255
        shg_norm = shg_norm.astype(np.uint8)
        filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_SHG.png'
        full_filename =  shg_png_path / filename    
        # io.imsave(full_filename, shg_norm)
        ScaleBar(shg, zoomFactor, scaleBarSize, 'r', full_filename)
        
        
        tpf_norm = tpf / np.max(tpf)
        tpf_norm *= 255
        tpf_norm = tpf_norm.astype(np.uint8)
        filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_TPEF.png'
        full_filename =  tpf_png_path / filename    
        # io.imsave(full_filename, tpf_norm)
        ScaleBar(tpf, zoomFactor, scaleBarSize, 'r', full_filename)
        plt.close('all')
       
    if len(imgs.shape) == 5:
        
        if imgs.shape[0] > 2:
            print('\n Z STACK' + '\n')
            print('z stack step size = ' + str(zStackStep))
            
            for stackIdx in range (0,imgs.shape[0]):
                shg = imgs[stackIdx, 1, 0, :, :]
                tpf = imgs[stackIdx, 1, 1, :, :]
                shg[shg<0] = 0
                tpf[tpf<0] = 0
                
                shg_norm = shg / np.max(shg)
                shg_norm *= 255
                shg_norm = shg_norm.astype(np.uint8)
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{stackIdx:03}" + '_SHG.png'
                full_filename =  shg_png_zstackPath / filename    
                io.imsave(full_filename, shg_norm)
                # ScaleBar(shg_norm, 50/75, 100, 'r', full_filename)
                
                tpf_norm = tpf / np.max(tpf)
                tpf_norm *= 255
                tpf_norm = tpf_norm.astype(np.uint8)
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{stackIdx:03}" + '_TPEF.png'
                full_filename =  tpf_png_zstackPath / filename    
                io.imsave(full_filename, tpf_norm)
                
                
            shgStack = imgs[:,1,0,:,:]
            tpfStack = imgs[:,1,1,:,:]
            from slice_viewer import sliceViewer
            sliceViewer(tpfStack, zStackStep, 'gray')
                
                
        else:
            print('alpha' + '\n')
            for idx2 in range(0,int(numberOfImages/2)):
                shg = imgs[1,2*idx2, :, :]
                tpf = imgs[1,2*idx2-1, :, :]
                shg[shg<0] = 0
                tpf[tpf<0] = 0
                
    
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG.tiff'
                full_filename =  shg_path / filename    
                io.imsave(full_filename, shg)
                if addScaleBar == True:
                    filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG_SCALE_BAR.tiff'
                    full_filename =  shg_path / filename    
                    ScaleBar(shg, zoomFactor, scaleBarSize, 'r', full_filename)
                
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF.tiff'
                full_filename =  tpf_path / filename    
                io.imsave(full_filename, tpf)
                if addScaleBar == True:
                    filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF_SCALE_BAR.tiff'
                    full_filename =  tpf_path / filename    
                    ScaleBar(tpf, zoomFactor, scaleBarSize, 'r', full_filename)
                
                shg_norm = shg / np.max(shg)
                shg_norm *= 255
                shg_norm = shg_norm.astype(np.uint8)
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG.png'
                full_filename =  shg_png_path / filename    
                io.imsave(full_filename, shg_norm)
                
                if addScaleBar == True:
                    filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG_SCALE_BAR.png'
                    full_filename =  shg_png_path / filename    
                    ScaleBar(shg_norm, zoomFactor, scaleBarSize, 'r', full_filename)
                
                
                tpf_norm = tpf / np.max(tpf)
                tpf_norm *= 255
                tpf_norm = tpf_norm.astype(np.uint8)
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF.png'
                full_filename =  tpf_png_path / filename    
                io.imsave(full_filename, tpf_norm)
                if addScaleBar == True:
                    filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF_SCALE_BAR.png'
                    full_filename =  tpf_png_path / filename    
                    ScaleBar(tpf_norm, zoomFactor, scaleBarSize, 'r', full_filename)
                plt.close('all')
    
    elif len(imgs.shape) == 4:
        print(' Bravo')
        for idx2 in range(0,int(numberOfImages/2)):
            shg = imgs[1,0,:,:]
            tpf = imgs[1,1,:,:]

            shg[shg<0] = 0
            tpf[tpf<0] = 0
            
    
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG.tiff'
            full_filename =  shg_path / filename    
            io.imsave(full_filename, shg)
            
            if addScaleBar == True:
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_SHG_SCALE_BAR.tiff'
                full_filename =  shg_path / filename    
                ScaleBar(shg, zoomFactor, scaleBarSize, 'r', full_filename)
            
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF.tiff'
            full_filename =  tpf_path / filename    
            io.imsave(full_filename, tpf)
            
            if addScaleBar == True:
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx1:03}" + '_TPF_SCALE_BAR.tiff'
                full_filename =  tpf_path / filename    
                ScaleBar(tpf, zoomFactor, scaleBarSize, 'r', full_filename)
            
            shg_norm = shg / np.max(shg)
            shg_norm *= 255
            shg_norm = shg_norm.astype(np.uint8)
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG.png'
            full_filename =  shg_png_path / filename    
            io.imsave(full_filename, shg_norm)
            
            if addScaleBar == True:
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_SHG_SCALE_BAR.png'
                full_filename =  shg_png_path / filename    
                ScaleBar(shg_norm, zoomFactor, scaleBarSize, 'r', full_filename)
            
            tpf_norm = tpf / np.max(tpf)
            tpf_norm *= 255
            tpf_norm = tpf_norm.astype(np.uint8)
            filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF.png'
            full_filename =  tpf_png_path / filename    
            io.imsave(full_filename, tpf_norm)
            
            if addScaleBar == True:
                filename = os.fsdecode(os.path.splitext(files_tiff[idx1])[0]) +'__'+ f"{idx2:03}" + '_TPEF_SCALE_BAR.png'
                full_filename =  tpf_png_path / filename    
                ScaleBar(tpf_norm, zoomFactor, scaleBarSize, 'r', full_filename)
            plt.close('all')
            
# plt.close('all')
path = os.path.realpath(data_path)
os.startfile(path)

 
