'''
ex2: draw contours in pockets
'''
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import cv2
import numpy as np
import scipy.spatial.distance as scid
import suGraph
import css
import pathengine

colors = pathengine.suPath2D.generate_RGB_list(15)
iColor = 0

def draw_iso_contour_id(pe, iso_contours_2D, font_size=0):
    
    for i in range(len(iso_contours_2D)):
        pathengine.suPath2D.draw_text(str(i + 1), iso_contours_2D[i][0], pe.im) 
        #pathengine.suPath2D.draw_line(iso_contours_2D[i], pe.im,[128,128,128],1)   
    
def draw_css_on_contour(pe, contour, w_size):
    kappa, smooth = css.compute_curve_css(contour, 4)
    css_idx = css.find_css_point(kappa)
    for i in css_idx:
        cv2.circle(pe.im, tuple(contour[i].astype(int)), 2, colors[3], -1)       
    return
def test_fill_from_CSS(filepath, offset, is_reverse_img=True):
    pe = pathengine.pathEngine()   
    def dfs_draw_contours_in_pocket(i, nodes, iso_contours_2D, spirals, offset):
        global colors
        global iColor
        node = nodes[i]  
        msg = '{} make spiral {}'.format(i+1, np.asarray(node.data) + 1)
        print(msg)  
        cs = []
        for ii in node.data:
            cs.append(iso_contours_2D[ii])
            c = pathengine.suPath2D.resample_curve_by_equal_dist(iso_contours_2D[ii], 4) 
            c = np.asarray(c)
            c = np.vstack((c, c[0]))
            pathengine.suPath2D.draw_line(c, pe.im, colors[iColor],1)    
        iColor += 1
        print("iColor={}".format(iColor))
        
        #spirals[i] = pe.build_spiral_for_pocket(cs) 
        if(len(node.next) > 0): 
            for ic in node.next:
                dfs_draw_contours_in_pocket(ic, nodes, iso_contours_2D, spirals, offset)         
        return
    
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
        iso_contours = pe.fill_closed_region_with_iso_contours(boundary, offset)        
        iso_contours_2D, graph = pe.init_isocontour_graph(iso_contours)   
        graph.to_Mathematica("")
        if not graph.is_connected():
            print("not connected")
            ret = pe.reconnect_from_leaf_node(graph, iso_contours, abs(offset * 1.2))
            if(ret):
                print("re-connect...")
                graph.to_Mathematica("")
        # generate a minimum-weight spanning tree
        graph.to_reverse_delete_MST()
        graph.to_Mathematica("")
        # generate a minimum-weight spanning tree
        pocket_graph = graph.gen_pockets_graph()
        pocket_graph.to_Mathematica("")        
        
        dfs_draw_contours_in_pocket(0, pocket_graph.nodes, iso_contours_2D, {}, offset)   
        
        draw_iso_contour_id(pe, iso_contours_2D)
        #show CSS points
        #for c in iso_contours_2D:
            #draw_css_on_contour(pe, c, 1)
            
        iB += 1     
    cv2.imwrite("r:/im1.png", pe.im)
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)   
    
if __name__ == '__main__':  

    test_fill_from_CSS("E:/git/suCAM/python/images/slice-1.png", -10, True) 