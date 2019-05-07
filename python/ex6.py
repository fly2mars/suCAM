"""
A test for generating continous tool path.
The procedure contains steps:
- load mesh
- analyze
- slicing
- traversal access
- sort and output a deque which includes boudaries of all connected area
example:
   ex6 --stl-file frameguide.stl --output-path images --slice-layers 5
"""
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import os, argparse, datetime
import cv2
from stl import mesh
import modelInfo
import stl2pngfunc
from collections import deque
import pathengine
import numpy as np
import scipy.spatial.distance as scid
import pyclipper
from suDataStructure import *

def remove_files(dir, ext='.png'):
    '''
    remove all file where extension=ext under dir
    if dir not exist, then create it
    @dir a current relative path
    @ext file extension

    example:
       remove_files("image")
    ''' 
    if(os.path.isdir(dir)):
        filelist = [ f for f in os.listdir(dir) if f.endswith(ext) ]            
        for f in filelist:
            os.remove(os.path.join(dir, f))  
    else:
        os.mkdir(dir)    
    return
def get_region_boundary_from_img(img_path, pe, is_reverse=False):
    '''
    @image_path is an obsolute file path
    @pe is a reference of patheEngine object
    @is_reverse is paramether for generate_contours_from_img
    @return
       a list, each element represents a group of boundaries of a connected region.
    '''
    pe.generate_contours_from_img(img_path, is_reverse)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree()
    group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')
    #closed region
    cs_region_list = []
    for cs_region in group_boundary.values():
        #resample
        for i in range(len(cs_region)):
            cs_region[i] = pathengine.suPath2D.resample_curve_by_equal_dist(cs_region[i], 4) 
        cs_region_list.append(cs_region)
    return cs_region_list

def is_interference(d, i, j, thresh):
    '''
    @d is regions deque
    @i current id of layer
    @j current id of region 
    @thresh is a distance threshold

    @return
      True: interference 
      False: not interference 
    '''
    #print("({}, {})".format(i,j))
    is_interfere = False
    r1 = d.get_item(i,j)
    rs, js = d.get_items(i)
    for idx in range(len(rs)):
        if js[idx] != j:
            pid_c1, pid_c2, min_dist = get_min_dist(r1, rs[idx])
            if min_dist < thresh:
                return True

    return False

def get_min_dist(b1, b2):
    """
    @b1 and b2 are contours of the 1-th boundary and 2-th boundary
    """
    def combine_contour(b):
        cs = []
        for idx in range(len(b)):
            if len(cs) == 0:
                cs = b[idx]
            else:
                np.vstack((cs, b[idx]))
        return cs
    b1 = combine_contour(b1)
    b2 = combine_contour(b2)

    dist = scid.cdist(b1, b2, 'euclidean')
    min_dist = np.min(dist)    
    gId = np.argmin(dist)
    pid_c1 = int(gId / dist.shape[1])
    pid_c2 = gId - dist.shape[1] * pid_c1            
    return pid_c1, pid_c2, min_dist    



#######################################################    
# ref: https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def area(p):
    p = list(p)
    return 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in segments(p)))
def segments(p):
    return zip(p, p[1:] + [p[0]])
def compute_region_area(r):
    a = 0                
    for i in range(len(r)):
        if pathengine.suPath2D.ccw(r[i]):
            a = a - area(r[i])
        else:
            a = a + area(r[i])
    return a  
def get_offset_contour(cs, offset):
    """
    get_ffset_contour(cs, -4)
    """
    pco = pyclipper.PyclipperOffset()
    pco.AddPaths(cs, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    ncs = pco.Execute(offset)
    return ncs
def find_surpported_region_in_layer(d, r, layer_id, offset = 8):
    """
    Given a r(i,j), find the upper connected.
    We compute the ratio = intersection_area(r_bottom, r_top) / area(r_top)
    to estimate the relationship of bottom-up region
    todo: check geometric feature

    Rules:      
      - i+1 inter offset contour area Ai
      - Ai intersect with i and get area I
      - if Ai == I then i+1 is supported by i
    Method:
      - use clipper to calculate intersection area
    """
    j = -1
    r_b = r
    r_t = []
    r_j = -1
    for idx in range(len(d.di)):
        ii = d.di[idx] 
        if ii == layer_id:         
            jj = d.dj[idx]
            r_t = d.d[idx]
            r_t = get_offset_contour(r_t, offset)       # use offset contour
            inter_sec = intersect_area(r_b, r_t)
            ratio = 0
            if len(inter_sec) != 0:                
                a = compute_region_area(inter_sec)
                b = compute_region_area(r_t)
                ratio = a / b
            if ratio > 0.95:
                return r_t, jj

    return r_t, r_j 



def intersect_area(r1, r2):
    """
    return the contours of the intersection area of r1 and r2
    @r1 consists contours of an region in layer i
    @r2 consists contours of an region in layer i + 1
    """    
    pc = pyclipper.Pyclipper()
    pc.AddPaths(r1, pyclipper.PT_CLIP, True)
    pc.AddPaths(r2, pyclipper.PT_SUBJECT, True)    
    solution = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)    
    return solution


def spiral(pe, boundary,offset):    
    spiral = pe.fill_spiral_in_connected_region(boundary, offset)
    spiral = pe.smooth_curve_by_savgol(spiral, 3, 1)
    #pathengine.suPath2D.draw_line(spiral, pe.im, [100,255,100],1)      
    
    return spiral
    
###########################
#@ms: a meshInfo object
###########################
def gen_continous_path(ms_info, tmp_slice_path, slice_layers, collision_dist = 3):
    dist_th = collision_dist
    N = slice_layers     
    m = ms_info
    m.set_layers(N)
    
    #slicing
    remove_files(tmp_slice_path)  
    curdir = os.getcwd()
    out_path = tmp_slice_path+"/slice-%d.png"  
    real_pixel_size, real_pixel_size, gcode_minx, gcode_miny = stl2pngfunc.stl2png(ms_info.path, N, m.image_width, 
                                                                                   m.image_height, out_path,
                        func = lambda i: print("slicing layer {}/{}".format(i+1,N))
                        )    
    #print sequence
    R = [] #R = {r_ij}
    S = [] #sequence with [[i,j]......]    
    pe = pathengine.pathEngine()  
    
    for i in range(N):
        img_file = out_path % i
        rs = get_region_boundary_from_img(img_file, pe, True)
        for r in rs:
            for c in r:
                print(c.shape)
        R.append(rs)     
    d = RDqueue(R)      #d = di = dj = deque() 
    r,i,j = d.get_end()
    while d.size() != 0:          
        if (i < N - 1) and (not is_interference(d, i, j, dist_th) ): 
            S.append([i,j])
            d.remove_item(i,j)            
            i = i + 1     
            r, j = find_surpported_region_in_layer(d, r, i, -6)

            if j == -1:   
                r, i, j = d.get_end() 
                continue
            if i == (N - 1): # reach the top
                if not is_interference(d, i, j, dist_th):
                    S.append([i,j])
                    d.remove_item(i,j)
                r,i,j = d.get_end()                
        else:
            r_next, i_next, j_next = d.get_end() 
            if [i,j] == [i_next, j_next]:  #the nozzle goes back and the region is not be appended
                S.append([i,j]) 
                d.remove_item(i,j)
                r_next, i_next, j_next = d.get_end()
            else:
                if i <= i_next: # The new region is not lower than current, 
                    S.append([i,j]) # so the nozzle doesn't need to go down. 
                    d.remove_item(i,j)
            r = r_next
            i = i_next
            j = j_next 
    # generate spiral and connect them
    d = RDqueue(R)    
    path = []
    Z = 0
    for i in range(0,len(S)-1):  
        r=d.get_item(S[i][0],S[i][1])
        cs=spiral(pe, r,-4)   * ms_info.get_pixel_size()
        #transformation to 3d vector
        z = [Z] * len(cs)
        z = np.array(z).reshape([len(z),1])        
        if i== 0:
            path = np.hstack([cs,z])
            Z += ms_info.first_layer_thickness
        else:
            cs = np.hstack([cs,z])
            path = np.vstack([path,cs])
            Z += ms_info.layer_thickness        
        
    
    return path
    
if __name__ == "__main__":
    # for visualization 
    colors = pathengine.suPath2D.generate_RGB_list(400)

    # parameters
    parser = argparse.ArgumentParser(description="Runs RMEC g-code generator.")
    parser.add_argument('--stl-file', dest='stl_file', required=True)
    parser.add_argument('--output-path', dest='output_path', required=False)
    parser.add_argument('--slice-layers', dest='N', required=False)
    args = parser.parse_args()
    
    N = 10
    file_path = "/"
    if args.N:
        N = int(args.N)
    if args.stl_file:
        file_path = args.stl_file
    if args.output_path:
        output_path = args.output_path
   
    # load stl
    ms = mesh.Mesh.from_file(file_path)
    m = modelInfo.ModelInfo(ms)
    m.path = file_path
    
    path = gen_continous_path(m, "r:/images", N, 3)
    print(path.shape)