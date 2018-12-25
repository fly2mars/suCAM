'''
This script provides an example for 
# 1. extract contours tree from mask image [simulating a layer of slices in STL model].
# 2. for each seperated region, generate iso-contours.
# 3. connect iso-contour to fermal spirals.
example:
          im, contours, areas, hiearchy, root_contour_idx = generate_contours_from_img(filename, isRevertBlackWhite)   
          contour_tree = convert_hiearchy_to_PyPolyTree()
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


####################################
# draw poly line to image # 
# point_list is n*2 np.ndarray #
####################################
def draw_line(point_lists, img, color, line_width=1):
    point_lists = point_lists.astype(int)
    pts = point_lists.reshape((-1,1,2))
    cv2.polylines(img, [pts], False, color, thickness=line_width, lineType=cv2.LINE_AA)
    cv2.imshow("Art", img)

#############################################
# Generate iso_contour from by clipper #
# https://github.com/greginvm/pyclipper #
# number of input contour: 0-n #
#############################################

def gen_internal_contour_by_clipper(contours, offset):
    
    pco = pyclipper.PyclipperOffset()
    pco.AddPaths(contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    solution = pco.Execute(offset)
    return solution

#############################################
# Generate iso_contour from by clipper #
# https://github.com/greginvm/pyclipper #
# number of input contour: 0-n #
#############################################
def gen_internal_contour_tree_by_clipper(contours, offset):
    pco = pyclipper.PyclipperOffset()
    pco.AddPaths(contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    polytree = pco.Execute2(offset)    
    return polytree
#######################################################################################
# return contours(python list by a tree) #
# https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
# This function provides:
# 1. Compute area for each contour
# 2. Return image, contours, areas, hiearchy, root_contour_idx 
#######################################################################################
def generate_contours_from_img(imagePath, isRevertImage=False):
    verts = []
    im = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
    if isRevertImage :
        im = 255 - im
    ret, thresh = cv2.threshold(im, 127, 255, 1)
    
    image, contours, hiearchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    
    # find contour with largest area
    idx = 0
    selectIdx = -1;
    area = 0
    areas = []
    if len(contours) > 0:
        for c in contours:
            a = cv2.contourArea(c)
            areas.append(a)
            if a > area:
                selectIdx = idx;
        verts = contours[selectIdx]
    return im, contours, areas, hiearchy, selectIdx  

# @cur_node: current node, first input is a empty root node
# @idx: current index    
def recusive_add_node(node, idx):
    global hiearchy
    global contours
    
    if idx >= hiearchy.shape[1]:
        return
    Next, Previous, First_Child, Parent = hiearchy[0][idx]    
    new_node = pyclipper.PyPolyNode()
    new_node.IsOpen = False
    new_node.IsHole = False    
    # add new node
    if First_Child != -1:
        new_node.Contour = contours[First_Child]
        new_node.Parent = node
        node.Childs.append(new_node)
        recusive_add_node(new_node, First_Child)
    if Next != -1:
            new_node.Contour = contours[Next]
            new_node.Parent = node.Parent
            new_node.Parent.Childs.append(new_node)
            recusive_add_node(new_node, Next)     
    return
###############################################################################
# Generate hiearchy tree from contours and hiearchy matrix
# Return contour tree
# TODO: recurent add node
# ref: http://www.angusj.com/delphi/clipper/documentation/Docs/Units/ClipperLib/Classes/PolyTree/_Body.htm
# ref: https://stackoverflow.com/questions/32182544/pyclipper-crash-on-trivial-case-terminate-called-throwing-an-exception
# ref: https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
###############################################################################
def convert_hiearchy_to_PyPolyTree():
    global hiearchy
    global contours
    # find first contour in hiearchy-0
    root = pyclipper.PyPolyNode()
    idx = -1
    for row in hiearchy[0]:
        Next, Previous, First_Child, Parent = row
        if Previous == -1 and Parent == -1:
            idx += 1
            node = pyclipper.PyPolyNode()
            node.Parent = root
            node.Contour = contours[idx]
            node.IsOpen = False
            node.IsHole = False                
            root.Childs.append(node)
            recusive_add_node(node, idx)
            break
    return root
#######################################
# Traversing a PyPolyTree
# @root: root of tree
# @order: 0-deep first, 1-breath first
# @func: function(contour, Children_list)
#######################################
def traversing_PyPolyTree(root, order=0, func=None):
    if (func != None):
        func(root.Contour, root.Childs)
    else:
        print("I have " + str(len(root.Childs)) + " children.")
    
    #TODO: add breath first traversing
    if (order == 0 ):
        for n in root.Childs:
            traversing_PyPolyTree(n, 0, func)        
    return

#######################################
# Remove small contours 
#######################################
def get_valid_contours(contours, areas, hiearchy, root_contour_index):
    vc = []
    for i in range(0, len(contours) ):
        if(areas[i] > 5):
            vc.append(contours[i])
            
    return vc

#######################################
# Generate N color list
#################################
def generate_RGB_list(N):
    import colorsys
    HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    rgb_list = tuple(RGB_tuples)
    return np.array(rgb_list) * 255


######################################
# Resample List (N < input_size/2) #
# input_list: contour in m*2 ndarray #
######################################
def resample_list(input_list, N):
    input_size = input_list.shape[0]
    N = N if N < input_size/2 else int(input_size/2)
    Sample = np.linspace(0, input_size, N, dtype = int, endpoint=False)   
    out_list = input_list[Sample]
    return out_list        
#############################################
# Recursively generate iso contour #
#############################################
def generate_iso_contour(contour, offset, is_draw = False):
    global gContours
    global im
    img = im
    inter_contour = gen_internal_contour_by_clipper(contour, offset) 
    N = len(inter_contour)
    if N != 0:
        for c in inter_contour:
            cc = np.array(c)
            if(is_draw):
                draw_line(np.vstack([cc, cc[0]]), img, [0,255,0])
            gContours.append(cc)
        
        generate_iso_contour(inter_contour, offset, is_draw)

###################################################################################
# Recursively generate iso contour 
# @contours: outter and inner contours
# @offset: minus value means inward offset
# return: build a contour tree for construct connected fermat's curve.           
# example:
#         contour_tree = convert_hiearchy_to_PyPolyTree()
#         group_contour = get_contours_from_each_connected_region(contour_tree, '0')
#         for cs in group_contours.value():
#             cij = generate_iso_contour_from_region(cs, -1)
###################################################################################
def generate_iso_contour_from_region(contours, offset, is_draw = False):
    pco = pyclipper.PyclipperOffset()
    pco.AddPaths(contours, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    contour_tree = pco.Execute2(offset)
    return contour_tree
   
def prev_idx(idx, contour):    
    if idx > 0:
        return idx - 1;
    if idx == 0:
        return len(contour) -1

def next_idx(idx, contour):
    if idx < len(contour)-1:
        return idx + 1
    if idx == len(contour) - 1:
        return 0
#######################################
# find nearest index of point in a contour
# @in: point value(not index), a contour
# @out: the index of a nearest point
#####################################
def find_nearest_point_idx(point, contour):
    idx = -1
    distance = float("inf")   
    for i in range(0, len(contour)-1):        
        d = np.linalg.norm(point-contour[i])
        if d < distance:
            distance = d
            idx = i
    return idx
##########################################################################
#find an index of point from end, with distance larger than T
#@in: current index of point, current contour, 
#@in: T is a distance can be set to offset or offset/2 or 2 * offset
##########################################################################
def find_point_index_by_distance(cur_point_index, cur_contour, T):
    T = abs(T)
    start_point = cur_contour[cur_point_index]
    idx_end_point = prev_idx(cur_point_index, cur_contour)
    
    end_point=[]        
    for ii in range(0,len(cur_contour)-1):
        end_point = cur_contour[idx_end_point]
        distance=np.linalg.norm(start_point-end_point)            
        if distance > T:           
            break
        else:           
            idx_end_point = prev_idx(idx_end_point, cur_contour)  
    return idx_end_point

##############################################################
# @in: iso contours, index of start point, offset
# @out: a single poly
# If you want connect in then connect out,
# you can divide contours into two sets, and run it twice,
# then connect them.
##############################################################
def contour2spiral(contours, idx_start_point, offset):
    offset = abs(offset)
    cc = [] # contour for return
    N = len(contours)
    for i in range(N):
        contour1 = contours[i]        
        
        ## find end point(e1)
        idx_end_point = find_point_index_by_distance(idx_start_point, contour1, 2*offset)
        end_point = contour1[idx_end_point]
        
        # add contour segment to cc
        idx = idx_start_point
        while idx != idx_end_point:
            cc.append(contour1[idx])
            idx = next_idx(idx, contour1)   
        
        if(i == N-1): 
            break
        
        ## find s2   
        idx_start_point2 = find_nearest_point_idx(end_point, contours[i+1])         
        
        idx_start_point = idx_start_point2   
        
        
    return cc     

def connect_spiral(first_spiral, second_spiral, is_flip=True):
    s = []
    if is_flip:
        second_spiral = np.flip(second_spiral, 0)
        
    for i in range(len(first_spiral)):
        s.append(first_spiral[i])                 
    for i in range(len(second_spiral)):
        s.append(second_spiral[i])
    return s

from scipy.signal import savgol_filter
def smooth_curve_by_savgol(c, filter_width=5, polynomial_order=1):
    N = 10
    c = np.array(c)
    y = c[:, 1]
    x = c[:, 0]
    x2 = savgol_filter(x, filter_width, polynomial_order)
    y2 = savgol_filter(y, filter_width, polynomial_order)
    c = np.transpose([x2,y2])
    return c

######################################
# Resample a curve by Roy's method
# "http://www.morethantechnical.com/2012/12/07/resampling-smoothing-and-interest-points-of-curves-via-css-in-opencv-w-code/"
# @contour: input contour
# @N: size of resample points
# @is_open: True means openned polyline, False means closed polylien
######################################
def resample_curve_by_equal_dist(contour, N, is_open = False):
    resample_c = []
    ## compute length of contour
    contour_length = 0;   
    
    for i in range(len(contour) - 1):
        d = np.linalg.norm(contour[i+1]-contour[i])
        contour_length += d
        
    if is_open == False:
        d = np.linalg.norm(contour[0] - contour[-1])
        contour_length += d
    
    resample_size = contour_length / N   
    
    dist = 0             # dist = cur_dist_to_next_original_point + last_original_dist
    cur_id = 0           # for concise
    resample_c.append(contour[0])
    
    nCount = len(contour) - 1
    if is_open == False:      
        nCount = len(contour)
        
    for i in range(nCount): 
        next_id = next_idx(cur_id, contour)
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
        
    return resample_c

################################################################################
# for each seperated region on a slice
#  - fill with connect spiral
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
def get_contours_from_each_connected_region(polyTreeNode, sId = '0'):
    root = polyTreeNode
    contour_group = {}  # eg. contour_group[id] holds all inner and outter contours in a seperated region.
    nDeep = sId.count('-')                        
    #for root node
    if (nDeep == 0):
        iChild = 0
        for n in polyTreeNode.Childs:
            cur_id = sId + '-' + str(iChild)
            cGroup = get_contours_from_each_connected_region(n, cur_id)
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
                    cGroup = get_contours_from_each_connected_region(n, cur_id)
                    # merge dict to contour_group
                    contour_group.update(cGroup)  
                    ii += 1                
        contour_group[sId] = contours        
        
    return contour_group

################################################################################
# for each connected region, fill with specified pattern 
# @contours: outter and inner contours
# @
################################################################################
def fill_connected_region(contour_group, offset):
    for cs in contour_group.value():
        generate_iso_contour(solution, offset, True)
    return


####################################################################################################################################
#                                 Main functions list
####################################################################################################################################
########################################################################
# main1 functionis original test
########################################################################
def main1():
    global hiearchy
    global contours
    global gContours
    global im
    #im, contours, areas, hiearchy, root_contour_idx = generate_contours_from_img("E:/git/suCAM/python/images/slice-1.png", True)
    im, contours, areas, hiearchy, root_contour_idx = generate_contours_from_img("E:/git/mydoc/Code/python/gen_path/data/honeycomb.png")
    height, width = im.shape[0], im.shape[1]             # picture's size
    img = np.zeros((height, width, 3), np.uint8) + 255   # for demostration
    
    print(hiearchy)
    #vc = get_valid_contours(contours, areas, hiearchy, root_contour_idx) # remove contours that area < 5 (estimated value)
    vc = contours
    color_list = generate_RGB_list(int(200/np.abs(offset))) # for demo    
         
    solution = [] # input contours: include outer shape contours and inner hole contours
                  # Here's a problem: slice regions may be seperated, eg. there are several outer shape contours.
                  # So I use a contour tree to tracking these contours, like [#debug 1.1] is doing.
    for idx in range(0, len(vc)):
        c = np.reshape(vc[idx], (vc[idx].shape[0],2))
        #c = resample_list(c, len(c)/1)     
        c = resample_curve_by_equal_dist( c, nSample)
        c = np.flip(c,0)    # reverse index order
        solution.append(c)    
    

    #debug 1.1: generate a contour tree for each slice. 
    contours = solution
    contour_tree = convert_hiearchy_to_PyPolyTree()
    traversing_PyPolyTree(contour_tree)
    group_contour = get_contours_from_each_connected_region(contour_tree, '0')
    for e in group_contour.keys():
        print(e)
    iRegion = 0   
    for v in group_contour.values():
        iRegion += 10
        for i in range(len(v)):        
            for ii in range(len(v[i])):        
                cv2.circle(img,tuple(v[i][ii].astype(int)), 4, color_list[iRegion], -1)        
    #for each seprated region
    #for i in range(len(contour_tree.Childs)):        
        #for ii in range(len(contour_tree.Childs[i].Contour)):        
            #cv2.circle(img,tuple(contour_tree.Childs[i].Contour[ii].astype(int)), 4, (0, 0, 255), -1)
    
    gContours.append(solution[0])            ## !!only one inputed contour
    
    # Tool path planning problem:
    # TODO: segment contours first then fill pattern into    
    generate_iso_contour(solution, offset, True)
    
    #inter
    for ii in range(len(gContours)):          
        gContours[ii] = resample_curve_by_equal_dist( gContours[ii], nSample)
        
    #connect
    ## divide contours into two groups(by odd/even)
    in_contour_groups = []
    out_contour_groups = []
    for idx in range(len(gContours)):
        if (idx % 2 == 0):
            in_contour_groups.append(gContours[idx])
        else:
            out_contour_groups.append(gContours[idx])
            
    
    cc_in = contour2spiral(in_contour_groups, 0, offset )
    output_index = find_nearest_point_idx(in_contour_groups[0][0], out_contour_groups[0]) 
           
    cc_out = contour2spiral(out_contour_groups, output_index, offset )
    
    ## connect two spiral
    fspiral = connect_spiral(cc_in, cc_out)
    ## set out point
    out_point_index = find_point_index_by_distance(0, in_contour_groups[0], offset)
    fspiral.append(in_contour_groups[0][out_point_index])   
    ## smooth withe filter size 3, order 1
    fspiral = smooth_curve_by_savgol(fspiral, 3, 1)
    draw_line(np.array(fspiral), img, [255, 0, 0], 1) 
    
    #draw point
    cv2.circle(img,tuple(in_contour_groups[0][0].astype(int)), 4, (0, 0, 255), -1)
    cv2.circle(img,tuple(in_contour_groups[0][out_point_index].astype(int)), 4, (0, 0, 255), -1)
  
    cv2.imshow("Art", img)
    cv2.imwrite("r:/unorderded.jpg", img)
    cv2.waitKey(0)               
    return
########################################################################
# main2 function demostrates how extract contours tree
########################################################################
def main2(filename):
    global hiearchy
    global contours
    
    im, contours, areas, hiearchy, root_contour_idx = generate_contours_from_img(filename, isRevertBlackWhite)   
    
    contour_tree = convert_hiearchy_to_PyPolyTree() 
    traversing_PyPolyTree(contour_tree)
    return  




if __name__ == '__main__':
    offset = -4 # inner offset
    nSample = 100 # number of resample vertices
    gContours = []
    hiearchy = None
    contours = []
    img = None
 
    main1()
                                                                                                                                          
    
    