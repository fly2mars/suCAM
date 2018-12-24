'''
This module provides functions about filling path generation 
# 1. extract contours tree from mask image [simulating a layer of slices in STL model].
# 2. for each seperated region, generate iso-contours.
# 3. connect iso-contour to fermal spirals.
example:
          im, contours, areas, hiearchy, root_contour_idx = generate_contours_from_img(filename, isRevertBlackWhite)   
          traversing_PyPolyTree(contour_tree)
          group_contour = get_contours_from_each_connected_region(contour_tree, '0')
          for e in group_contour.values():
              ePath = gen_isocontours(e)
              ePath = gen_fermat_curve(ePath)

In 3D printing path generation,    
'''

import cv2
import numpy as np
import pyclipper

class pathEngine:
    def __init__(self):
        self.offset = 0.4
        self.im = None
        self.contours = None
        self.areas = None
        self.hiearchy = None        
        return
    
    #######################################################################################
    # return contours(python list by a tree) #
    # https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    # This function provides:
    # 1. Compute area for each contour
    # 2. Return image, contours, areas, hiearchy, root_contour_idx 
    #######################################################################################
    def generate_contours_from_img(imagePath, isRevertImage=False):        
        im = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
        if isRevertImage :
            im = 255 - im
        ret, thresh = cv2.threshold(im, 127, 255, 1)
        
        self.image, self.contours, self.hiearchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return self.image, self.contours, self.hiearchy
    
    