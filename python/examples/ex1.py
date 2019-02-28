'''
ex1: Generate and draw continous path
'''
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import pathengine
import cv2
import numpy as np
import scipy.spatial.distance as scid
import suGraph
import css

def find_nearest_point_for_css(c1, c2, offset, window_size = 4):
    """
    find CSS points on c1
    make a polyline by above points
    find nearest pair of index
    @c1 is the first contour
    @c2 is the second contour
    @windows_size is \alpha of CSS
    """
    id1 = id2 = -1
    kappa, smooth = css.compute_curve_css(c1, 4)  
    css_idx = css.find_css_point(kappa)
    c = []
    for i in css_idx:
        c.append(c1[i])
    id1, id2, min_d = pathengine.suPath2D.find_closest_point_pair(c,c2)
    if min_d < abs(offset) * 1.1:
        return id1, id2
    else:
        return -1, -1
    
    
    
def test_fill_from_CSS(filepath, offset, is_reverse_img=True):
    pe = pathengine.pathEngine()   
    
    #1.find contours from slice
    pe.generate_contours_from_img(filepath, is_reverse_img)

    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')    

    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    #2.filling each connected region   
    dist_th = abs(offset) * 1.1 # contour distance threshold between adjacent layers
    iB = 0
    for boundary in group_boundary.values():
        print("Region {}: has {} boundry contours.".format(iB, len(boundary)) )
        spiral = pe.fill_spiral_in_connected_region(boundary, offset)        
    
        spiral = pe.smooth_curve_by_savgol(spiral, 3, 1)
        pathengine.suPath2D.draw_line(spiral, pe.im, [100,255,100],1)                      

        #debug: draw all spiral 
        #id_sp = 0
        #kappa, smooth = css.compute_curve_css(spiral, 4)  
        #css_idx = css.find_css_point(kappa)
        #for i in css_idx:
            #cv2.circle(pe.im, tuple(spiral[i].astype(int)), 2, (255,255,0), -1)    

        iB += 1     

    cv2.imwrite("r:/fig4-c.png", pe.im)
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)   
    
if __name__ == '__main__':  

    test_fill_from_CSS("E:/git/suCAM/python/images/slice-1.png", -10, True) 