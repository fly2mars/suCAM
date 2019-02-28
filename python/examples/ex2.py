'''
ex2: draw spiral in pockets
'''
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from pathengine import *
import cv2
import numpy as np
import scipy.spatial.distance as scid
import suGraph
import css
import pathengine


colors = suPath2D.generate_RGB_list(20)
def test_fill_from_CSS(filepath, offset, is_reverse_img=True):
    pe = pathengine.pathEngine()   
    def dfs_connect_path_from_bottom(i, nodes, iso_contours_2D, spirals, offset):
        node = nodes[i]  
        msg = '{} make spiral {}'.format(i+1, np.asarray(node.data) + 1)
        print(msg)  
        cs = []
        for ii in node.data:
            cs.append(iso_contours_2D[ii])
        spirals[i] = pe.build_spiral_for_pocket(cs, True) 
        if(len(node.next) > 0): 
            for ic in node.next:
                dfs_connect_path_from_bottom(ic, nodes, iso_contours_2D, spirals, offset)         
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
        # init contour graph for iso contour by a distance relationaship matrix  
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
        # generate spiral for each pockets
        # deep first search
        spirals = {}
        dfs_connect_path_from_bottom(0, pocket_graph.nodes, iso_contours_2D, spirals, offset)
        
        i = 0
        for s in spirals.values():
            pathengine.suPath2D.draw_line(s, pe.im, colors[i],1)   
            i = i + 1
  
        #debug: draw all spiral 
        if len(spirals) < 2:
            continue
        id1 = 9
        kappa, smooth = css.compute_curve_css(spirals[id1], 4)  
        css_idx = css.find_css_point(kappa)
        for i in css_idx:
            cv2.circle(pe.im, tuple(spirals[id1][i].astype(int)), 2, colors[id1], -1)                                       

        id2 = 8
        kappa, smooth = css.compute_curve_css(spirals[id2], 4)  
        css_idx = css.find_css_point(kappa)
        for i in css_idx:
            cv2.circle(pe.im, tuple(spirals[id2][i].astype(int)), 2, colors[id2], -1)     
        
        id2 = 5
        kappa, smooth = css.compute_curve_css(spirals[id2], 4)  
        css_idx = css.find_css_point(kappa)
        for i in css_idx:
            cv2.circle(pe.im, tuple(spirals[id2][i].astype(int)), 2, colors[id2], -1)            
        
        #debug: connect two pockets
        #s = test_connect_two_pockets(pe, spirals[id1], spirals[id2], offset)
        pathengine.suPath2D.draw_line(s, pe.im, colors[5],1) 
        
            
        iB += 1     

    cv2.imshow("Art", pe.im)
    cv2.imwrite("r:/222.png", pe.im)
    cv2.waitKey(0)   
    
if __name__ == '__main__':  

    test_fill_from_CSS("E:/git/suCAM/python/images/slice-1.png", -10, True) 