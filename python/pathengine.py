"""
This module provides functions about filling path generation
# 1. extract contours tree from mask image [simulating a layer of slices in STL model].
# 2. for each seperated region, generate iso-contours.
# 3. connect iso-contour to fermal spirals.
example:
          pe = pathEngine()
          im, contours, areas, hiearchy, root_contour_idx = pe.generate_contours_from_img(filename, isRevertBlackWhite)  
          contour_tree = pe.convert_hiearchy_to_PyPolyTree()
          pe.traversing_PyPolyTree(contour_tree)
          group_contour = get_contours_from_each_connected_region(contour_tree, '0')
          for e in group_contour.values():
              ePath = gen_isocontours(e)
              ePath = gen_fermat_curve(ePath)

In 3D printing path generation,   
"""

import cv2
import numpy as np
import pyclipper
import math
import scipy.spatial.distance as scid
import suGraph
from scipy.signal import savgol_filter
import css

class suPath2D:
    """
    Hold data structure and tool functions for 2D path
    """    
    def __init__(self):        
        self.contour_tree      = None
        self.group_boundary    = []
        self.group_isocontours = []  #containts iso contours list
        self.group_isocontours_2D = []
        self.group_relationship_matrix = []
        
        return 
    @staticmethod
    def get_contour_id(i,j,iso_contours):
        """
        Get a 1D global index from iso_contours list contour(i,j), where
        i is the distance to the boundary, there are many contours(j=0...n-1).  
        Thus we can generate a index matrix for building a graph that can
        be visualized in different tools. Eg.
        Mathematica:
           GraphPlot[{{1, 1, 1, 0}, {1, 0, 0, 0}, {0, 1, 0, 0}, {1, 1, 0, 1}},
                     SelfLoopStyle -> True, MultiedgeStyle -> True,
                     VertexLabeling -> True, DirectedEdges -> True]
        """
        id = 0 
        ii = 0
        for cs in iso_contours:
            if ii == i: break
            for c in cs:
                id += 1
            ii += 1           
        id += j # indexed from 0
        return id   
    @staticmethod
    def prev_idx(idx, contour):
        """ Returns next point id for a closed contour.  """
        if idx > 0:
            return idx - 1;
        if idx == 0:
            return len(contour) -1
    @staticmethod
    def next_idx(idx, contour):
        """ Returns previous point id for a closed contour.  """
        if idx < len(contour)-1:
            return idx + 1
        if idx == len(contour) - 1:
            return 0
    @staticmethod
    def next_idx_n(idx, n, contour):
        for i in range(n):
            idx = suPath2D.next_idx(idx, contour)
        return idx
    @staticmethod
    def prev_idx_n(idx, n, contour):
        for i in range(n):
            idx = suPath2D.prev_idx(idx, contour)
        return idx    
    @staticmethod
    def unit_vector(vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector)  
    @staticmethod
    def angle_between(v1, v2):
        """ 
        Returns the angle in dgree between vectors 'v1' and 'v2'
    
        example:
            angle_between((1, 0, 0), (0, 1, 0))
            90.0
            angle_between((1, 0, 0), (1, 0, 0))
            0.0            
        """
        v1_u = suPath2D.unit_vector(v1)
        v2_u = suPath2D.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)) / math.pi * 180
    
    @staticmethod
    def convto_cw(contours):
        for i in range(len(contours)):
            if( suPath2D.ccw(contours[i]) ):
                contours[i] = np.flip(contours[i], 0)
    @staticmethod
    def find_distance_matrix(cs):
        """ 
        compute distance matrix and min distance among a group of contours
        return distance matrix and the index of the min value
        
        example:
             D, i,j= find_distance_matrix(contours)
        """ 
        n = len(cs)
        D = np.zeros([n,n])
        d = float("inf")
        idx_i, idx_j = 0, 0
        
        for i in range(n):
            for j in range(n):
                if(i != j):
                    t1,t2,D[i][j] = suPath2D.find_closest_point_pair(cs[i],cs[j])
                    if D[i][j] < d:
                        d = D[i][j]
                        idx_i, idx_j = i, j
        return D, idx_i, idx_j          
    @staticmethod
    def resample_curve_by_equal_dist(contour, size=2, is_open = False):
        """ 
        Resample a curve by Roy's method
        Refer to "http://www.morethantechnical.com/2012/12/07/resampling-smoothing-and-interest-points-of-curves-via-css-in-opencv-w-code/"
        @contour: input contour
        @size: sample size on the contour
        @is_open: True means openned polyline, False means closed polylien
        example:
             c = suPath2D.resample_curve_by_equal_dist( c, offset)     
        """ 
        resample_c = []
        ## compute length of contour
        contour_length = 0;  
        contour = np.asarray(contour)
        for i in range(len(contour) - 1):
            d = np.linalg.norm(contour[i+1]-contour[i])
            contour_length += d
           
        if is_open == False:
            d = np.linalg.norm(contour[0] - contour[-1])
            contour_length += d
       
        resample_size = size 
        N = int(contour_length / resample_size)
        if (N < 10):  #avoid lost in smooth
            N = 10
            resample_size = contour_length / 4
       
        dist = 0             # dist = cur_dist_to_next_original_point + last_original_dist
        cur_id = 0           # for concise
        resample_c.append(contour[0])
       
        nCount = len(contour) - 1
        if is_open == False:     
            nCount = len(contour)
           
        for i in range(nCount):
            next_id = suPath2D.next_idx(cur_id, contour)
            last_dist = np.linalg.norm(contour[next_id]-contour[i])
            dist += last_dist    #current length
            if(dist >= resample_size):
                #put a point on line
                d_ = last_dist - (dist - resample_size)    #reserve size
                dir_ = contour[next_id] - contour[cur_id]
               
                new_point = contour[cur_id] + d_ * dir_ / np.linalg.norm(dir_)
                resample_c.append(new_point)
               
                dist = last_dist - d_  #remaining dist
               
                #if remaining dist to next point needs more sampling...
                while (dist - resample_size > 1e-3):
                    new_point = resample_c[-1] + resample_size * dir_ / np.linalg.norm(dir_)
                    resample_c.append(new_point)               
                    dist -= resample_size              
                   
            cur_id = next_id
        #print(resample_c)  
        return  np.asarray(resample_c)   
    @staticmethod
    def find_closest_point_pair(c1, c2):
        """
        Return two indice of the closest pair of points.
        
        example:
            id1, id2, min_d = find_closest_point_pair(c1,c2)
        """
        dist = scid.cdist(c1, c2, 'euclidean')
        min_dist = np.min(dist)    
        gId = np.argmin(dist)
        pid_c1 = int(gId / dist.shape[1])
        pid_c2 = gId - dist.shape[1] * pid_c1            
        return pid_c1, pid_c2, min_dist

    @staticmethod
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
        id1, id2, min_d = suPath2D.find_closest_point_pair(c,c2)
        return css_idx[id1], id2, min_d 
    @staticmethod
    def draw_line(point_lists, img, color, line_width=1, point_size=0):
        """
        draw poly line to image 
        point_list is a np.ndarray with shape of (n,2)
        example:
           suPath2D.draw_text(str(i + 1), iso_contours_2D[i][0], pe.im)
        """
        if len(point_lists) == 0:
            return
        point_lists = point_lists.astype(int)
        pts = point_lists.reshape((-1,1,2))
        cv2.polylines(img, [pts], False, color, thickness=line_width, lineType=cv2.LINE_AA)
        #cv2.imshow("Art", img)
        if point_size != 0:
            for p in point_lists:
                cv2.circle(img, tuple(p), point_size, color)   
        return
    def draw_text(text, bottom_left, img, fontColor = (255,0,0), fontScale = 0.5, lineType=1):
        """
        example:
           suPath2D.draw_text(str(i + 1), iso_contours_2D[i][0], pe.im)
        """
        font                   = cv2.FONT_HERSHEY_SIMPLEX
        fontSize               = [12,-12]
        offset = bottom_left - np.array(fontSize)*fontScale
        cv2.putText(img,text,
            tuple(offset.astype(int)) ,
            font,
            fontScale,
            fontColor,
            lineType)
        return

    @staticmethod
    def generate_RGB_list(N):
        """
        Generate N color list
        """
        import colorsys
        HSV_tuples = [(x*1.0/N, 0.8, 0.9) for x in range(N)]
        RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
        rgb_list = tuple(RGB_tuples)
        return np.array(rgb_list) * 255   
    
    @staticmethod
    def ccw(contour):
        """
        check a contour is (counter clockwise)CCW or CW
        return CCW: True   CW: False
        refer to https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
        Here we use openCV image coordinate, like HTML5 canvas
        """
        l = np.asarray(contour)
        ls = np.roll(l, -1, axis=0)
        
        a = np.sum( (ls[:,0] - l[:,0])*(ls[:,1] + l[:,1]) )
        if a<0:
            return False
        return True
    
class pathEngine:
    """
    Class pathEngine provide all necessary functions to build continous path.
    """
    def __init__(self):
        self.offset = 0.4
        self.im = None
        self.contours = None
        self.areas = None
        self.hiearchy = None 
        self.path2d = suPath2D()
        self.root_of_region_contour = None
        self.iso_contours_of_a_region = []
        return

    def generate_contours_from_img(self, imagePath, isRevertImage=False):    
        """
        Read image from imagePath and return 
        @im reprents a image data
        @contours(python list of list)
        @hiearchy reprensents a matrix, the details can be find in https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
        """
        im = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
        if isRevertImage :
            im = 255 - im
        ret, thresh = cv2.threshold(im, 127, 255, 1)
       
        self.im, self.contours, self.hiearchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return self.im, self.contours, self.hiearchy

    def recusive_add_node(self, node, idx):
        """
        This function  recursively add a child node add a brother node 
        into current node based on the hiearchy matrix. The detail 
        can be refered to https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
        return 
        @cur_node: current node, first input is a empty root node
        @idx: current index   
        Note: In each node, the shape of contour from opencv is converted from (x,1,2) to (x,2)
        """
       
        if idx >= self.hiearchy.shape[1]:
            return
        Next, Previous, First_Child, Parent = self.hiearchy[0][idx]   
        new_node = pyclipper.PyPolyNode()
        new_node.IsOpen = False
        new_node.IsHole = False   
        # add new node
        if First_Child != -1:
            new_node.Contour = self.contours[First_Child].reshape((-1,2)) # (x rows, 1, 2) -> (x rows, 2)               
            new_node.Parent = node
            node.Childs.append(new_node)
            self.recusive_add_node(new_node, First_Child)
        if Next != -1:
                new_node.Contour = self.contours[Next].reshape((-1,2))
                new_node.Parent = node.Parent
                new_node.Parent.Childs.append(new_node)
                self.recusive_add_node(new_node, Next)    
        return   

    def convert_hiearchy_to_PyPolyTree(self):
        """
        Build a root node and find first level node in hiearchy, then add these node to root. 
        Finally, use recusive_add_node(node,0) to generate hiearchy tree.
        Return contour tree (in PyPolyNode)
        ref: http://www.angusj.com/delphi/clipper/documentation/Docs/Units/ClipperLib/Classes/PolyTree/_Body.htm
        ref: https://stackoverflow.com/questions/32182544/pyclipper-crash-on-trivial-case-terminate-called-throwing-an-exception  
        """
        # find first contour in hiearchy-0
        root = pyclipper.PyPolyNode()
        idx = -1
        for row in self.hiearchy[0]:
            Next, Previous, First_Child, Parent = row
            if Previous == -1 and Parent == -1:
                idx += 1
                node = pyclipper.PyPolyNode()
                node.Parent = root        
                node.Contour = self.contours[idx].reshape((-1,2))  # (x rows, 1, 2) -> (x rows, 2)                   
                node.IsOpen = False
                node.IsHole = False               
                root.Childs.append(node)
                self.recusive_add_node(node, idx)
                break
        self.root_of_region_contour = root
        return root  
   

    def get_contours_from_each_connected_region(self, polyTreeNode, sId = '0'):
        """
        for each seperated region on a slice
        - return contour group to represent boundaries of a connected region
          each seperated region represents a region with connected area.
        @polyTreeNode is used to hold region boundary. Typically, the boundaries
                    stored in the current node represent external contours, and
                    the contours stored in the child nodes represent the internal
                    contours, such as holes. If child nodes have their own children
                    that will represent new seperated regions. We can deal these cases
                    by the recursive process.
        @sId is the id of polyTreeNode, eg. 0(root), 0-1(first child of root),
                    0-1-2(second grandson of root)
        @return a dict, @contour_group, each key-value represents a seperate regon KEY
                    and its boundary contours.
        
        examples:   contour_group = get_contours_from_each_connected_region(root, '0')
                    contour_group = get_contours_from_each_connected_region(node, '0-1-1')
        """
        root = polyTreeNode
        contour_group = {}  # eg. contour_group[id] holds all inner and outter contours in a seperated region.
        nDeep = sId.count('-')                       
        #for root node
        if (nDeep == 0):
            iChild = 0
            for n in polyTreeNode.Childs:
                cur_id = sId + '-' + str(iChild)
                cGroup = self.get_contours_from_each_connected_region(n, cur_id)
                # merge dict to contour_group
                contour_group.update(cGroup)  
                iChild += 1
        #for layer contains outer contour
        if (nDeep % 2 == 1):
            iChild = 0       
            contours = []
            contours.append(polyTreeNode.Contour) #outer contour
            #for layers contains inner contour
            for n in polyTreeNode.Childs:
                cur_id = sId + '-' + str(iChild)
                contours.append(n.Contour)
                iChild += 1           
                #next layer
                ii = 0
                for c in n.Childs:
                        child_id = cur_id + '-' + str(ii)
                        cGroup = self.get_contours_from_each_connected_region(n, cur_id)
                        # merge dict to contour_group
                        contour_group.update(cGroup) 
                        ii += 1               
            contour_group[sId] = contours       
           
        return contour_group   
   

    def traversing_PyPolyTree(self, root, func=None, order=0):
        """
        A function for test.
        Traversing a PyPolyTree
        @root: root of tree
        @func: function(contour, Children_list)
        @order: 0-deep first, 1-breath first(TODO)
        
        """
        if (func != None):           
            func(root)
        else:
            if(root.Parent == None):
                print("-----")
            msg = "Node {} has {} child node".format(root.depth, len(root.Childs))
            print(msg)
             
        if (order == 0 ):  # deep first
            for n in root.Childs:
                self.traversing_PyPolyTree(n, func, 0)
        return  
   

    def get_nodes_by_layer(self, node, depth):
        """
        A test function(not used again)
        Get all nodes that depth = nDepth from a PyPolyTree
        @depth: depth of node
        return a list of node where node.depth = depth   
        """
        node_list = []       
        def traverse(node,depth, node_list):
            for n in node.Childs:
                if (n.depth == depth):
                    node_list.append(n)
                    continue
                else:
                    traverse(n,depth,node_list)
            return
             
        traverse(node, depth, node_list)
        return node_list
           
    def fill_closed_region_with_iso_contours(self, input_contours, offset):
        """
        fill a region with iso contours
        add all contours into self.iso_contours_of_a_region
        return @iso_contours_of_a_region, which inclues
        an iso contour list, each is represented as c[i,j]
        example:
              pe = pathEngine()
              pe.generate_contours_from_img(filepath, True)
              contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
              group_contour = pe.get_contours_from_each_connected_region(contour_tree, '0')
              for cs in group_contour.values():
                  pe.iso_contours_of_a_region.clear()
                  iso_contours = pe.fill_closed_region_with_iso_contours(cs, offset)
        
        """
        self.offset = offset
        iso_contours_of_a_region = []
        contours = input_contours
        iso_contours_of_a_region.append(input_contours)
        while(len(contours) != 0):
            pco = pyclipper.PyclipperOffset()
            pco.AddPaths(contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            contours = pco.Execute(offset)           
            iso_contours_of_a_region.append( contours)
        return iso_contours_of_a_region

    def find_nearest_point_idx(self, point, contour):
        """
        given a point, find the nearest index of point in a contour
        @point(a value, not index) is a vertex
        @contours 
        return the index of a nearest point
        """
        idx = -1
        distance = float("inf")   
        for i in range(0, len(contour)-1):        
            d = np.linalg.norm(point-contour[i])
            if d < distance:
                distance = d
                idx = i
        return idx   
    
    def find_point_index_by_distance(self, cur_point_index, cur_contour, T, ori=1):
        """
        find an index of point from current point, which distance larger than T
        @in: current index of point, current contour, 
        @in: T is a distance can be set to offset or offset/2 or 2 * offset
        @ori: orientation ori = 1 prev order, ori = 0 next order
        """
        T = abs(T)
        start_point = cur_contour[cur_point_index]
        
        if (ori):
            idx_end_point = suPath2D.prev_idx(cur_point_index, cur_contour)
        else:
            idx_end_point = suPath2D.next_idx(cur_point_index, cur_contour)
        end_point=[]        
        for ii in range(0,len(cur_contour)-1):
            end_point = cur_contour[idx_end_point]
            distance=np.linalg.norm(start_point-end_point)            
            if distance > T:           
                break
            else:           
                #idx_end_point = suPath2D.prev_idx(idx_end_point, cur_contour) 
                if (ori):
                    idx_end_point = suPath2D.prev_idx(idx_end_point, cur_contour)
                else:
                    idx_end_point = suPath2D.next_idx(idx_end_point, cur_contour)                
        return idx_end_point    
    
    def contour2spiral(self, contours, idx_start_point, offset):
        """
        Connect all contours of a pocket. The key idea is divide contours 
        into two sets, and run the connection process twice, one for in
        the other for out. Then connect them again.
        @contours: iso contours, index of start point, offset
        @idx_start_point: start connect at idx_start_point-th point on contours[0] 
        """
        offset = abs(offset)
        cc = [] # contour for return
        N = len(contours)
        for i in range(N):
            contour1 = contours[i]        
            
            ## find end point(e1)
            idx_end_point = self.find_point_index_by_distance(idx_start_point, contour1, offset)
            end_point = contour1[idx_end_point]
                
            # add contour segment to cc
            idx = idx_start_point
            while idx != idx_end_point:
                cc.append(contour1[idx])
                idx = suPath2D.next_idx(idx, contour1)   
            
            if(i == N-1): 
                break          
            
            ## find s2   
            idx_start_point2 = self.find_nearest_point_idx(end_point, contours[i+1])  
            # go forward a distance to avoid interference
            idx_start_point2 = self.find_point_index_by_distance(idx_start_point2, contours[i+1], offset/2, 0)
            
            idx_start_point = idx_start_point2                  
            #cv2.circle(self.im, tuple(contours[i][idx_end_point].astype(int)), 5, (255,0,0), -1)                      
        return cc     
    
    def connect_spiral(self, first_spiral, second_spiral, is_flip=True):
        """
        Connect two spiral
        @is_flip means if the orientation of second contour needs to be changed.
        Commonly, we reverse the orientation of second contour, then connect it
        with the first one.                
        """
        s = []
        if is_flip:
            second_spiral = np.flip(second_spiral, 0)
            
        for i in range(len(first_spiral)):
            s.append(first_spiral[i])                 
        for i in range(len(second_spiral)):
            s.append(second_spiral[i])
        return s
    # return contours 2d list
    # init a graph for organizing iso-contours
    def init_isocontour_graph(self, iso_contours):
        """
        Generate 2d iso contour list and a graph by distance relationship matrix
        @iso_contours includes list of contours[i,j] 
        return
          @iso_contours_2D
          @graph
        """
        num_contours = 0       
        iso_contours_2D = []
        # contour distance threshold between adjacent layers
        dist_th = abs(self.offset) * 1.2  
        inter_size = abs(self.offset)/6
        if inter_size < 4:
            inter_size = 4

        for i in range(len(iso_contours)):
            for j in range(len(iso_contours[i])):
                # resample && convert to np.array                
                iso_contours[i][j] = suPath2D.resample_curve_by_equal_dist(iso_contours[i][j], inter_size) 
                iso_contours_2D.append(iso_contours[i][j])               
                num_contours += 1       
        suPath2D.convto_cw(iso_contours_2D)
        # @R is the relationship matrix
        R = np.zeros((num_contours, num_contours)).astype(int)    
        i = 0
        for cs in iso_contours[:-1]:     # for each group contour[i], where i*offset reprents the distance from boundaries      
            j1 = 0           
            for c1 in cs:               
                c1_id = suPath2D.get_contour_id(i, j1, iso_contours)  

                j2 = 0
                for c2 in iso_contours[i+1]:
                    dist = scid.cdist(c1, c2, 'euclidean')
                    min_dist = np.min(dist)
                    if(min_dist < dist_th):
                        c2_id = suPath2D.get_contour_id(i+1, j2, iso_contours)
                        R[c1_id][c2_id] = 1

                    j2 += 1
                j1 += 1
            i += 1       
        #visualize
        graph = suGraph.suGraph()  
        graph.init_from_matrix(R)        
        return iso_contours_2D, graph    
    
    def reconnect_from_leaf_node(self, graph, iso_contours, dist_thresh):
        """
        if graph not connected, find new edge from leaf nodes.
        return true if the re-connection is successful
        Method: Just add a new edge, if the graph is connected, then return
        example:
            ret = reconnect_from_lear_node(graph, iso_contours)
        """
        layer = range(len(iso_contours)-1)
        layer = list(layer)
        layer.reverse()
        for l in layer: # check from leaf nodes
            cs = iso_contours[l]
            D, i, j = suPath2D.find_distance_matrix(cs)
            if(D[i,j] < dist_thresh):
                global_ind_i = suPath2D.get_contour_id(l, i, iso_contours)
                global_ind_j = suPath2D.get_contour_id(l, j, iso_contours)
                graph.nodes[global_ind_i].next.append(global_ind_j)
                graph.nodes[global_ind_j].pre.append (global_ind_i)
                graph.update_matrix()
                if(graph.is_connected()):                
                    return True
        return  False    
    
    def connect_two_pockets(self, fc1, fc2, offset):
        """
        connect to the next contour then going back
        connect points:
                        start                    end
           fc1:    pid_c1(closest)         goning forward with distance offset (from start)
           fc2:    pid_c2(closest)         going forward and contrary to the dir of fc1, end near the start of fc1 
        """        
        pid_c1, pid_c2, min_d = suPath2D.find_nearest_point_for_css(fc1, fc2, offset)
        if(min_d > abs(offset) * 1.1):
            pid_c1, pid_c2, min_d = suPath2D.find_closest_point_pair(fc1,fc2)
        
        
        # check orientation
        # not precise, todo: use log func to estimate
        n_forward = 1
        #if(len(fc1) > 1000 and len(fc2) > 1000):
            #n_forward = 1
        nid_c1 = self.path2d.next_idx_n(pid_c1, n_forward, fc1)
        nid_c2 = self.path2d.next_idx_n(pid_c2, n_forward,fc2)
        dir_fc1 = fc1[nid_c1] - fc1[pid_c1]
        dir_fc2 = fc2[nid_c2] - fc2[pid_c2]
        angle = suPath2D.angle_between(dir_fc1, dir_fc2)
        
        fc = []
        #find return point with distance to pid_c1 = offset
        pid_c1_return = self.find_point_index_by_distance(pid_c1, fc1, offset, 0)
                
        
        #fc1 from 0 to pid_c1
        #for i in range(pid_c1+1):
            #fc.append(fc1[i]) 
        fc = fc + list(fc1)[0:pid_c1+1]
        #get returned index from fc2
        pid_c2_near_return = self.find_nearest_point_idx(fc1[pid_c1_return], fc2)
        
            #if (idx_end == pid_c2):
                #print(">>>>")
                #idx_end = suPath2D.next_idx(idx_end, fc2)
        
        #test
        #cv2.circle(self.im, tuple(fc1[pid_c1].astype(int)), 2, (0,0,255))          
        #cv2.circle(self.im, tuple(fc2[pid_c2_near_return].astype(int)), 2, (255,0,0)) 
        
        idx = pid_c2
        if angle > 90:
            # different orientaton: 
            if (pid_c2_near_return == pid_c2):
                #print("-------------------------------------------")
                #cv2.circle(self.im, tuple(fc2[idx_end].astype(int)), 2, (0,0,255)) 
                pid_c2_near_return = self.find_point_index_by_distance(pid_c2_near_return, fc2, offset, 1)            
            while idx != pid_c2_near_return:  
                fc.append(fc2[idx])
                idx = self.path2d.next_idx(idx, fc2)            
        else:
            if (pid_c2_near_return == pid_c2):
                #print("-------------------------------------------")
                
                pid_c2_near_return = self.find_point_index_by_distance(pid_c2_near_return, fc2, offset, 0)            
            while idx != pid_c2_near_return:  
                fc.append(fc2[idx])
                idx = self.path2d.prev_idx(idx, fc2)            
                
        
        fc.append(fc2[pid_c2_near_return])
        # 3        
        fc = fc + list(fc1[pid_c1_return:])
            
        return np.asarray(fc)    
    def test_connect_two_pockets(self, fc1, fc2, offset):
        """
        connect to the next contour then going back
        connect points:
                        start                    end
           fc1:    pid_c1(closest)         goning forward with distance offset (from start)
           fc2:    pid_c2(closest)         going forward and contrary to the dir of fc1, end near the start of fc1 
        """        
        # Firstval, use the original start and end point of fc2
        pid_c2 = len(fc2) - 1
        #pid_c1, pid_c2 = suPath2D.find_closest_point_pair(fc1,fc2)
        
        pid_c1 = self.find_nearest_point_idx(fc2[pid_c2], fc1)
        d = np.linalg.norm(fc1[pid_c1]-fc2[pid_c2])
        #test
        d = 3*offset
        if(d > 2*offset):
            pid_c1, pid_c2, min_d = suPath2D.find_closest_point_pair(fc1,fc2)
        
        # check orientation
        # not precise, todo: use log func to estimate
        n_forward = 1
        #if(len(fc1) > 1000 and len(fc2) > 1000):
            #n_forward = 1
        nid_c1 = self.path2d.next_idx_n(pid_c1, n_forward, fc1)
        nid_c2 = self.path2d.next_idx_n(pid_c2, n_forward,fc2)
        dir_fc1 = fc1[nid_c1] - fc1[pid_c1]
        dir_fc2 = fc2[nid_c2] - fc2[pid_c2]
        angle = suPath2D.angle_between(dir_fc1, dir_fc2)
        
        fc = []
        #find return point with distance to pid_c1 = offset
        pid_c1_return = self.find_point_index_by_distance(pid_c1, fc1, offset, 0)
                
        
        #fc1 from 0 to pid_c1
        #for i in range(pid_c1+1):
            #fc.append(fc1[i]) 
        fc = fc + list(fc1)[0:pid_c1+1]
        #get returned index from fc2
        pid_c2_near_return = self.find_nearest_point_idx(fc1[pid_c1_return], fc2)
        
            #if (idx_end == pid_c2):
                #print(">>>>")
                #idx_end = suPath2D.next_idx(idx_end, fc2)
        
        #test
        cv2.circle(self.im, tuple(fc1[pid_c1].astype(int)), 2, (0,0,255))          
        cv2.circle(self.im, tuple(fc2[pid_c2_near_return].astype(int)), 2, (255,0,0)) 
        
        idx = pid_c2
        if angle > 90:
            # different orientaton: 
            if (pid_c2_near_return == pid_c2):
                #print("-------------------------------------------")
                cv2.circle(self.im, tuple(fc2[idx_end].astype(int)), 2, (0,0,255)) 
                pid_c2_near_return = self.find_point_index_by_distance(pid_c2_near_return, fc2, offset, 1)            
            while idx != pid_c2_near_return:  
                fc.append(fc2[idx])
                idx = self.path2d.next_idx(idx, fc2)            
        else:
            if (pid_c2_near_return == pid_c2):
                #print("-------------------------------------------")
                
                pid_c2_near_return = self.find_point_index_by_distance(pid_c2_near_return, fc2, offset, 0)            
            while idx != pid_c2_near_return:  
                fc.append(fc2[idx])
                idx = self.path2d.prev_idx(idx, fc2)            
                
        
        fc.append(fc2[pid_c2_near_return])
        # 3        
        fc = fc + list(fc1[pid_c1_return:])
            
        return np.asarray(fc)  
    def dfs_connect_path_from_bottom(self, i, nodes, iso_contours_2D, spirals, offset):
            node = nodes[i]  
            msg = '{} make spiral {}'.format(i+1, np.asarray(node.data) + 1)
            print(msg)  
            cs = []
            for ii in node.data:
                cs.append(iso_contours_2D[ii])
            spirals[i] = self.build_spiral_for_pocket(cs, False) 
    
            #if(i ==7):
            #    suPath2D.draw_line(spirals[i], self.im, [255,255,0],1)
            if(len(node.next) > 0): 
                for ic in node.next:
                    self.dfs_connect_path_from_bottom(ic, nodes, iso_contours_2D, spirals, offset)                    
    
                    if (len(spirals[ic]) / len(spirals[i]) > 2):
                        spirals[i] = self.connect_two_pockets(spirals[ic],spirals[i], abs(offset))
                        msg = '{} insert {}'.format(ic+1, i+1)
                        print(msg)                        
                    else:
                        spirals[i] = self.connect_two_pockets(spirals[i],spirals[ic], abs(offset))
                        msg = '{} insert {}'.format(i+1, ic+1)
                        print(msg)                        
    
    
            return      
    def fill_spiral_in_connected_region(self, boundary, offset):
        
        iso_contours = self.fill_closed_region_with_iso_contours(boundary, offset)
        # init contour graph for iso contour by a distance relationaship matrix  
        iso_contours_2D, graph = self.init_isocontour_graph(iso_contours)     
        graph.to_Mathematica("")

        if not graph.is_connected():
            print("not connected")
            ret = self.reconnect_from_leaf_node(graph, iso_contours, abs(offset * 1.2))
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
        self.dfs_connect_path_from_bottom(0, pocket_graph.nodes, iso_contours_2D, spirals, offset) 
        
        return spirals[0]        
    def smooth_curve_by_savgol(self, c, filter_width=5, polynomial_order=1):
        #N = 10
        last_vert = c[-1]
        c = np.array(c)
        y = c[:, 1]
        x = c[:, 0]
        x2 = savgol_filter(x, filter_width, polynomial_order)
        y2 = savgol_filter(y, filter_width, polynomial_order)
        c = np.transpose([x2,y2])
        c = np.vstack((c,last_vert))
            
        return c    
   
    @staticmethod
    def check_pocket_ratio_by_pca(cs,offset=4):
        """
        return ratio, start_point_idx by Principal Component Analysis(PCA)    
        @ratio = second component / first component
        @start_point_idx speicify an entrance position by PCA
        input
        @cs: contour list in pockets
        @offset: to determin distance of interpolation 
        """
        from sklearn.decomposition import PCA
        verts = []
        for c in cs:
            for p in c:
                verts.append(p)
        verts = np.array(verts).reshape([len(verts),2])    
        pca = PCA(n_components=2)
        pca.fit(verts)
    
        v = []
        l = []
        for length, vector in zip(pca.explained_variance_, pca.components_):
            sqrt_len = np.sqrt(length) 
            v.append(vector * 3 * sqrt_len)
            l.append(sqrt_len)
        ratio = l[1] / l[0]     
        # find a index of point in cs[0] that is nearest to axes <pca.mean, pca.mean + v[1]>
        # interpolation on line <pca.mean, pca.mean + v[1]>
        ax1 = []
        ax1.append(pca.mean_)
        ax1.append(pca.mean_ + v[1])
        ax1 = suPath2D.resample_curve_by_equal_dist(ax1, abs(offset)/2)
        pid_c1, pid_c2, d = suPath2D.find_closest_point_pair(cs[0],ax1)
        
        return ratio, pid_c1    
    def build_spiral_for_pocket(self, iso_contours, use_PCA = False):
        """
        Split contours into two groups(by odd/even), connect each then join these two spirals.
        @iso_contours: input iso contours of a pocket  
        return a spiral path
        """
        if (len(iso_contours) == 1):
            return iso_contours[0]        
        in_contour_groups = []
        out_contour_groups = []
        for idx in range(len(iso_contours)):
            if (idx % 2 == 0):
                in_contour_groups.append(iso_contours[idx])
            else:
                out_contour_groups.append(iso_contours[idx])
    
        #test
        start_id = 0
        if use_PCA:
            ratio, entrance_id = pathEngine.check_pocket_ratio_by_pca(in_contour_groups, self.offset)        
            if (ratio < 0.8):
                start_id = entrance_id
        #cv2.circle(self.im, tuple(in_contour_groups[0][start_id].astype(int)), 5, (0,0,255)) 
        
        cc_in = self.contour2spiral(in_contour_groups,start_id, self.offset )
        output_index = self.find_nearest_point_idx(in_contour_groups[0][start_id], out_contour_groups[0]) 
        
        #test
        #cv2.circle(self.im, tuple(out_contour_groups[0][output_index].astype(int)), 5, (0,0,255)) 
        
        cc_out = self.contour2spiral(out_contour_groups, output_index, self.offset )
    
        ## connect two spiral
        fspiral = self.connect_spiral(cc_in, cc_out)
        ## set out point
        out_point_index = self.find_point_index_by_distance(start_id, in_contour_groups[0], self.offset/2)
        fspiral.append(in_contour_groups[0][out_point_index])     
        return np.array(fspiral)    
           
############################
# compute hausdorff distance
############################

def compute_hausdorff_distance(c1, c2):
    u = np.array(c1)
    v = np.array(c2)
    return scid.directed_hausdorff(u, v)[0]   

def test_tree_visit(filepath):     
    pe = pathEngine()   
    pe.generate_contours_from_img(filepath, True)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree()
   
    def func(node):
        contour = node.Contour
        if len(contour) == 0:
            return       
        draw_line(np.vstack([contour, contour[0]]), pe.im, (0,255,0),2)       
        return
    pe.traversing_PyPolyTree(contour_tree, func)  
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)               
    return

def test_region_contour(filepath):
    pe = pathEngine()   
    pe.generate_contours_from_img(filepath, True)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    group_contour = pe.get_contours_from_each_connected_region(contour_tree, '0')
   
    #######################################
    # Generate N color list
    #################################
    def generate_RGB_list(N):
        import colorsys
        HSV_tuples = [(x*1.0/N, 0.8, 0.9) for x in range(N)]
        RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
        rgb_list = tuple(RGB_tuples)
        return np.array(rgb_list) * 255  
    colors = generate_RGB_list(len(group_contour.values()))
    idx = 0
    for cs in group_contour.values():
        for c in cs:
            draw_line(np.vstack([c, c[0]]), pe.im, colors[idx],2)
        idx += 1
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)         
"""
pe.fill_closed_region_with_iso_contours(boundary, offset) return a 2d array c[i][j]
"""
def test_fill_with_iso_contour(filepath, reverseImage = True):
    offset = -6
    line_width = 1#int(abs(offset)/2)
    pe = pathEngine()   
    pe.generate_contours_from_img(filepath, reverseImage)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    group_contour = pe.get_contours_from_each_connected_region(contour_tree, '0')
         
    #draw boundaries
    #################################
    # Generate N color list
    #################################
    def generate_RGB_list(N):
        import colorsys
        HSV_tuples = [(x*1.0/N, 0.8, 0.9) for x in range(N)]
        RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
        rgb_list = tuple(RGB_tuples)
        return np.array(rgb_list) * 255  
    N = 50
    colors = generate_RGB_list(N)
   
    for boundary in group_contour.values():
        iso_contours = pe.fill_closed_region_with_iso_contours(boundary, offset)
        idx = 0
        for cs in iso_contours:
            for c in cs:
                suPath2D.draw_line(np.vstack([c, c[0]]), pe.im, colors[idx],line_width)
            idx += 1
    gray = cv2.cvtColor(pe.im, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY_INV |cv2.THRESH_OTSU)
    cv2.imshow("mask", mask)
    cv2.imwrite("r:/tmp.png", pe.im)  
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)             


  
if __name__ == '__main__':   
    #test_tree_visit("E:/git/suCAM/python/images/slice-1.png")
    #test_region_contour("E:/git/suCAM/python/images/slice-1.png")
    test_fill_with_iso_contour("E:/git/suCAM/python/images/slice-1.png")
    #test_segment_contours_in_region("E:/git/mydoc/Code/Python/gen_path/data/sample.png")
    #test_segment_contours_in_region("E:/git/suCAM/python/images/slice-1.png")
    