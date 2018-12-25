'''
This module provides functions about filling path generation 
# 1. extract contours tree from mask image [simulating a layer of slices in STL model].
# 2. for each seperated region, generate iso-contours.
# 3. connect iso-contour to fermal spirals.
example:
          pe = pathEngine()
          im, contours, areas, hiearchy, root_contour_idx = pe.generate_contours_from_img(filename, isRevertBlackWhite)   
          pe.traversing_PyPolyTree(contour_tree)
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
        self.root_of_region_contour = None
        self.iso_contours_of_a_region = None
        return
    
    #######################################################################################
    # return contours(python list by a tree) #
    # https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    # This function provides:
    # 1. Compute area for each contour
    # 2. Return image, contours, areas, hiearchy, root_contour_idx 
    #######################################################################################
    def generate_contours_from_img(self, imagePath, isRevertImage=False):           
        im = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
        if isRevertImage :
            im = 255 - im
        ret, thresh = cv2.threshold(im, 127, 255, 1)
        
        self.im, self.contours, self.hiearchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return self.im, self.contours, self.hiearchy
    #######################################################################################
    # Recursively add a child node and add a brother node by info from hiearchy
    # In each node, the contour from opencv is converted from (x,1,2) to (x,2)
    # @cur_node: current node, first input is a empty root node
    # @idx: current index    
    # ref: https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    #######################################################################################
    def recusive_add_node(self, node, idx):
        
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
    ###############################################################################
    # Generate hiearchy tree from contours and hiearchy matrix
    # Return contour tree
    # 1. construct a root node
    # 2. find the first parent contour and add it to the first child node[use recusive_add_node].
    # ref: http://www.angusj.com/delphi/clipper/documentation/Docs/Units/ClipperLib/Classes/PolyTree/_Body.htm
    # ref: https://stackoverflow.com/questions/32182544/pyclipper-crash-on-trivial-case-terminate-called-throwing-an-exception    
    ###############################################################################
    def convert_hiearchy_to_PyPolyTree(self):
        if self.hiearchy == None:
            return
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
    
    ################################################################################
    # for each seperated region on a slice
    #  - return contour group to reprent boundaries of a region
    # The seperated region means a region with connected area.
    # @polyTreeNode is used to hold region boundary. Typically, the boundaries 
    #               stored in the current node represent external contours, and 
    #               the contours stored in the child nodes represent the internal 
    #               contours, such as holes. If child nodes have their own children
    #               that will represent new seperated regions. We can deal these cases
    #               by the recursive process.
    # @sId is the id of polyTreeNode, eg. 0(root), 0-1(first child of root),
    #               0-1-2(second gradson of root)
    # @return a dict, @contour_group, each key-value represents a seperate regon KEY 
    #              and its boundary contours. 
    # examples:    contour_group = get_contours_from_each_connected_region(root, '0')
    #              contour_group = get_contours_from_each_connected_region(node, '0-1-1')
    ################################################################################
    def get_contours_from_each_connected_region(self, polyTreeNode, sId = '0'):
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
    
    #######################################
    # Traversing a PyPolyTree
    # @root: root of tree
    # @order: 0-deep first, 1-breath first
    # @func: function(contour, Children_list)
    #######################################
    def traversing_PyPolyTree(self, root, func=None, order=0):
        if (func != None):            
            func(root.Contour, root.Childs)
        else:
            if(root.Parent == None):
                print("-----")
            print("I have " + str(len(root.Childs)) + " children.")
              
        if (order == 0 ):  # deep first
            for n in root.Childs:
                self.traversing_PyPolyTree(n, func, 0)
        return   
    
    ##############################################
    # generate iso contour for a closed region
    ##############################################
    def generate_iso_contour(self, input_contours, parent_node, offset):                
        pco = pyclipper.PyclipperOffset()
        pco.AddPaths(input_contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        contour_tree = pco.Execute2(offset)        
        return contour_tree
    ##############################################
    # fill a region with iso contours
    # add all contours into self.iso_contours_of_a_region
    # example:
    #          
    ##############################################
    def fill_closed_region_with_iso_contours(self, input_contours, offset):
        if(len(input_contours) == 0):
            return []
        else:
            self.iso_contours_of_a_region = self.iso_contours_of_a_region + input_contors
            pco = pyclipper.PyclipperOffset()
            pco.AddPaths(input_contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            contours = pco.Execute(offset)
            self.fill_closed_region_with_iso_contours(input_contours, offset)
        return 

############################################################################################################
#                         Test Functions                                                                   #    
############################################################################################################    
####################################
# draw poly line to image # 
# point_list is n*2 np.ndarray #
####################################
def draw_line(point_lists, img, color, line_width=1):
    point_lists = point_lists.astype(int)
    pts = point_lists.reshape((-1,1,2))
    cv2.polylines(img, [pts], False, color, thickness=line_width, lineType=cv2.LINE_AA)
    #cv2.imshow("Art", img)
    return
    

def test_tree_visit(filepath):      
    pe = pathEngine()    
    pe.generate_contours_from_img(filepath, True)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree()
    
    def func(contour, children_node):
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

def test_fill_with_iso_contour(filepath):
    offset = -10
    line_width = int(abs(offset)/2)
    pe = pathEngine()    
    pe.generate_contours_from_img(filepath, True)
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
    colors = generate_RGB_list(len(group_contour.values()))
    idx = 0
    for cs in group_contour.values():
        for c in cs:
            draw_line(np.vstack([c, c[0]]), pe.im, colors[idx],line_width) 
        idx += 1
    
    #draw offset contours
    def func(contour, children_node):
        if len(contour) == 0:
            return        
        draw_line(np.vstack([contour, contour[0]]), pe.im, (np.random.randint(255),np.random.randint(255),np.random.randint(255)),line_width)
        return    
    parent_node = pyclipper.PyPolyNode()  #no used
    
    for cs in group_contour.values():
        tree = pe.generate_iso_contour(cs, parent_node, offset)
        pe.traversing_PyPolyTree(tree, func)
        pe.traversing_PyPolyTree(tree)
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)              
        
if __name__ == '__main__':    
    #test_tree_visit("E:/git/suCAM/python/images/slice-1.png")
    #test_region_contour("E:/git/suCAM/python/images/slice-1.png")
    test_fill_with_iso_contour("E:/git/suCAM/python/images/slice-1.png")