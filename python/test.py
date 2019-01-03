import pathengine
import cv2
import numpy as np
import scipy.spatial.distance as scid
import suGraph
'''
test hausdorff distanse in  construct graph on iso-contours
'''
def test_segment_contours_in_region(filepath):
    path2d = pathengine.suPath2D()
      
    offset = -14
    line_width = 1 #int(abs(offset)/2)
    pe = pathengine.pathEngine()   
    pe.generate_contours_from_img(filepath, True)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    path2d.group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')

    color = (255,0,0)   
   
   
    ## Build a init graph from boundaries
    # distance threshold between two adjacent layers
    dist_th = abs(offset) * 1.2    
    iB = 0
    for boundary in path2d.group_boundary.values():
        msg = "Region {}: has {} boundry contours.".format(iB, len(boundary))
        print(msg)
       
        iso_contours = pe.fill_closed_region_with_iso_contours(boundary, offset)       
       
        # init contour graph for each region
        num_contours = 0       
        iso_contours_2D = []
        for i in range(len(iso_contours)):
            for j in range(len(iso_contours[i])):
                # resample and convert to np.array
                iso_contours[i][j] = pe.resample_curve_by_equal_dist(iso_contours[i][j], abs(offset/2))            
                iso_contours_2D.append(iso_contours[i][j])
                num_contours += 1         
        # @R is the relationship matrix
        R = np.zeros((num_contours, num_contours)).astype(int)    
       

        # @input: iso_contours c_{i,j}
        i = 0
        for cs in iso_contours[:-1]:     # for each group contour[i], where i*offset reprents the distance from boundaries      
            j1 = 0           
            for c1 in cs:               
                c1_id = path2d.get_contour_id(i, j1, iso_contours)
               
                pathengine.suPath2D.draw_line(np.vstack([c1,c1[0]]), pe.im, color, 1, 2) 
                pathengine.suPath2D.draw_text(str(c1_id + 1), c1[0], pe.im, (0,0,255))
                j2 = 0
                for c2 in iso_contours[i+1]:
                    dist = scid.cdist(c1, c2, 'euclidean')
                    min_dist = np.min(dist)
                    #print(dist)
                    if(min_dist < dist_th):
                        c2_id = path2d.get_contour_id(i+1, j2, iso_contours)
                        R[c1_id][c2_id] = 1
                        #debug: get indexes of two closest points
                        gId = np.argmin(dist)
                        pid_c1 = int(gId / dist.shape[1])
                        pid_c2 = gId - dist.shape[1] * pid_c1
                        pathengine.suPath2D.draw_line(np.asarray([c1[pid_c1], c2[pid_c2]]), pe.im, (0,0,255), 1,0)
                       
                    j2 += 1
                j1 += 1
            i += 1       
        #visualize
        graph = suGraph.suGraph()
        #graph.init_from_matrix(R)       
        pockets = graph.classify_nodes_by_type(R)
        
        N = len(pockets)
        colors = path2d.generate_RGB_list(N)        
        p_id = 0       
        for p in pockets:
            print(np.array(p) + 1)
            for idx in p:
                pathengine.suPath2D.draw_line(np.vstack([iso_contours_2D[idx],iso_contours_2D[idx][0]]), pe.im, colors[p_id], 2, 4) 
            p_id += 1            
        
        
        path2d.group_isocontours.append(iso_contours)
        path2d.group_isocontours_2D.append(iso_contours_2D)
        path2d.group_relationship_matrix.append(R)
        iB += 1
        
        graph.to_Mathematica("")
   
   
    gray = cv2.cvtColor(pe.im, cv2.COLOR_BGR2GRAY)
    #ret, mask = cv2.threshold(gray, 1, 255,cv2.THRESH_BINARY)
    pe.im[np.where((pe.im==[0,0,0]).all(axis=2))] = [255,255,255]
    cv2.imwrite("d:/tmp.png", pe.im)
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)    
   


def connect_spiral(fc1, fc2):
    # from fc1 point 1
    # find nearest 
    
    return

def test_pocket_spiral(filepath, offset = -14, reverseImage = True):
    path2d = pathengine.suPath2D()

    line_width = 1 #int(abs(offset)/2)
    pe = pathengine.pathEngine()   
    pe.generate_contours_from_img(filepath, reverseImage)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    path2d.group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')
    
    ## Build a init graph from boundaries
    # contour distance threshold between adjacent layers
    dist_th = abs(offset) * 1.05

    iB = 0
    for boundary in path2d.group_boundary.values():
        msg = "Region {}: has {} boundry contours.".format(iB, len(boundary))
        print(msg)
        iso_contours = pe.fill_closed_region_with_iso_contours(boundary, offset) 
        
        # init contour graph for each region
        num_contours = 0       
        iso_contours_2D = []
        map_ij = []
        for i in range(len(iso_contours)):
            for j in range(len(iso_contours[i])):
                # resample and convert to np.array
                iso_contours[i][j] = pe.resample_curve_by_equal_dist(iso_contours[i][j], abs(offset)/4) 
                if(i == 0):
                    iso_contours_2D.append(np.flip(iso_contours[i][j],0))
                else:
                    iso_contours_2D.append(iso_contours[i][j])                
                
                map_ij.append([i,j])
                num_contours += 1         
        # @R is the relationship matrix
        R = np.zeros((num_contours, num_contours)).astype(int)    
        i = 0
        for cs in iso_contours[:-1]:     # for each group contour[i], where i*offset reprents the distance from boundaries      
            j1 = 0           
            for c1 in cs:               
                c1_id = path2d.get_contour_id(i, j1, iso_contours)  
                
                j2 = 0
                for c2 in iso_contours[i+1]:
                    dist = scid.cdist(c1, c2, 'euclidean')
                    min_dist = np.min(dist)
                    #print(dist)
                    if(min_dist < dist_th):
                        c2_id = path2d.get_contour_id(i+1, j2, iso_contours)
                        R[c1_id][c2_id] = 1
    
                    j2 += 1
                j1 += 1
            i += 1       
        #visualize
        graph = suGraph.suGraph()
        #graph.init_from_matrix(R)  
        #graph.simplify(map_ij)   
        pockets = graph.classify_nodes_by_type(R,map_ij)  
        #graph.to_Mathematica("")
        print(pockets)
        
        # gen spiral for each pocket
        spirals = []
        for p in pockets:
            cs = []
            for c_id in p:
                cs.append(iso_contours_2D[c_id])
                pe.path2d.draw_text(str(c_id + 1), iso_contours_2D[c_id][0], pe.im)
                    
            if(len(cs) !=0):
                spiral = pe.build_spiral_for_pocket(cs)  
                spirals.append(spiral)                
               
        color = [0,255,0]
        for p_id in range(len(pockets)):
            #node = graph.get_node(where_pocket_id = p_id)
            #if node.is_typeII():
                #connect_spiral(node_pre.pocket_id, p_id)
                #connect_spiral(node_next.pocket_id, p_id)
            if len(pockets[p_id]) == 1:
                color = [0,0,255]
            else:
                if pockets[p_id][0] == 37:
                    color = [255,0,0]
            path2d.draw_line(spirals[p_id], pe.im, color,1)
            
                    
        #path2d.draw_line(iso_contours_2D[37], pe.im, [0,0,255],2)
        #np.set_printoptions(threshold=np.inf)
        #print(R[37])
        #print(R.T[37])
        graph.to_Mathematica("")
        path2d.group_isocontours.append(iso_contours)
        path2d.group_isocontours_2D.append(iso_contours_2D)
        path2d.group_relationship_matrix.append(R)
        iB += 1
    
        graph.connect_node_by_spiral(spirals)
   
        
    gray = cv2.cvtColor(pe.im, cv2.COLOR_BGR2GRAY)
    pe.im[np.where((pe.im==[0,0,0]).all(axis=2))] = [255,255,255]
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)          
        

if __name__ == '__main__':  
    #test_segment_contours_in_region("E:/git/suCAM/python/images/slice-1.png")
    #test_pocket_spiral("E:/git/suCAM/python/images/slice-1.png")
    #test_pocket_spiral("E:/git/mydoc/Code/python/gen_path/data/two-circle.png", -10, False)
    test_pocket_spiral("E:/git/mydoc/Code/python/gen_path/data/sample.png", -10, False)
    #test_pocket_spiral("E:/git/suCAM/python/images/slice-1.png")