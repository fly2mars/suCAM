"""
A test for 3D slicing and global connection.
The procedure contains steps:
- load mesh
- analyze
- slicing
- traversal access
- sort and output a deque which includes boudaries of all connected area
example:
   ex4 --stl-file frameguide.stl --output-path images --slice-layers 5
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

def LOG(func):
    def wrap_log(*args, **kwargs):
        start_time = datetime.datetime.now()      
        try:
            func(*args) #running code specific to this job
        except Exception as e:
            print(e.message)

        end_time = datetime.datetime.now()
        print("Use time: {} ".format(end_time - start_time))

    return wrap_log    

@LOG
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
        #ccw to cw and vice versa
        #resample
        for i in range(len(cs_region)):
            cs_region[i] = np.flip(cs_region[i], 0)
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

class RDqueue():
    def __init__(self, R):
        """
        init with all regions in slices
        Note: It 
        """
        self.d = deque()
        self.di = deque()
        self.dj = deque()
        for i in range(len(R)):
            for j in range(len(R[i])):
                self.d.append(R[i][j])
                self.di.append(i)
                self.dj.append(j)         
        return
    def __len__(self):
        return len(self.d)
    def get_end(self):
        if len(self.di) > 0:
            r = self.d[0]
            i = self.di[0]
            j = self.dj[0]
            return r, i, j
        return [], sys.maxsize, -1

    def remove_end(self):
        self.d.popleft()
        self.di.popleft()
        self.dj.popleft()
        return
    def pop_end(self):
        r, i, j = self.get_end()
        if j != -1:
            self.remove_end()
        return
    def get_item(self, i, j):
        """
        Return r
        If r(i,j) is not found, return []
        """
        for idx in range(len(self.di)):
            if (self.di[idx] == i) and (self.dj[idx] == j ):
                return self.d[idx]
        return []
    def get_items(self, i):
        """
        return all r(i,*), js
        if not found return an empty list
        """
        rs = []     
        js = []
        for idx in range(len(d)):
            if self.di[idx] == i:
                rs.append(self.d[idx])
                js.append(self.dj[idx])
        return rs, js

    def remove_item(self, i, j):
        for idx in range(len(self.di)):
            if (self.di[idx] == i) and (self.dj[idx] == j ):                
                del self.di[idx]
                del self.dj[idx]
                del self.d[idx]
                break
        return

    def size(self):
        return len(self.d)    
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
            if ratio > 0.98:
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

def find_sequence_test(path):
    return

def calculate_dist_test(r1, r2):

    return

if __name__ == "__main__":
    # for visualization 
    colors = pathengine.suPath2D.generate_RGB_list(5)

    # parameters
    parser = argparse.ArgumentParser(description="Runs RMEC g-code generator.")
    parser.add_argument('--stl-file', dest='stl_file', required=True)
    parser.add_argument('--output-path', dest='output_path', required=False)
    parser.add_argument('--slice-layers', dest='N', required=False)
    args = parser.parse_args()

    N = 10
    file_path = ""
    if args.N:
        N = int(args.N)
    if args.stl_file:
        file_path = args.stl_file
    if args.output_path:
        output_path = args.output_path

    # load stl
    ms = mesh.Mesh.from_file(file_path)
    m = modelInfo.ModelInfo(ms)
    m.set_layers(N)
    #m.set_pixel_size(0.11)
    #m.set_image_size()

    print(m.get_info())

    image_width = 640
    image_height = 480

    #remove all files in images   
    remove_files(output_path)  
    curdir = os.getcwd()

    out_path = output_path+"/slice-%d.png"


    real_pixel_size, real_pixel_size, gcode_minx, gcode_miny = stl2pngfunc.stl2png(file_path, N, m.image_width, 
                        m.image_height, out_path,
                        func = lambda i: print("slicing layer {}/{}".format(i+1,N))
                        )

    print('Slicing mesh into ' + out_path)

    # algorithm   
    pe = pathengine.pathEngine()       

    #R = {r_ij}
    R = []

    for i in range(N):
        img_file = out_path % i
        rs = get_region_boundary_from_img(img_file, pe, True)        
        R.append(rs) #

    d = RDqueue(R)

    subj = (
        ((180, 200), (260, 200), (260, 150), (180, 150)),
        ((215, 160), (230, 190), (200, 190))
    )

    clip = ((190, 210), (240, 210), (240, 130), (190, 130))

    pc = pyclipper.Pyclipper()
    pc.AddPath(clip, pyclipper.PT_CLIP, True)
    pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)    
    solution = pc.Execute(pyclipper.CT_INTERSECTION)#, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD) 

    print(solution)

    im = np.zeros((640, 480, 1), dtype = "uint8")
    im = im + 255
    im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)

    lll = np.array(clip)
    ll = np.array(subj[1])
    l = np.array(subj[0])
    pathengine.suPath2D.draw_line(np.vstack((l,l[0])), im, colors[0],1)   
    pathengine.suPath2D.draw_line(np.vstack((ll,ll[0])), im, colors[1],1)  
    #pathengine.suPath2D.draw_line(np.vstack((lll,lll[0])), im, colors[2],1)  

    m = np.array(solution)

    i = 0
    for s in solution:
        ls = np.array(s)
        #pathengine.suPath2D.draw_line(np.vstack((ls,ls[0])), im, colors[3 + i],2)  
        i += 1

    pe.im = pe.im + 255
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)

    def draw_region(im, r, color = [255,0,0]):        
        for c in r:
            pathengine.suPath2D.draw_line(np.vstack((c,c[0])), im, color,1)  
    def draw_region_with_tag(im, r, color = [255,0,0], lw=1):        
        for c in r:            
            pathengine.suPath2D.draw_line(np.vstack((c,c[0])), im, color, lw)     
            if pathengine.suPath2D.ccw(c):
                pathengine.suPath2D.draw_text("CCW", c[0], im)
            else:
                pathengine.suPath2D.draw_text("CW", c[0], im)


    rs, js = d.get_items(1)
    ii = 0
    for r in rs:
        #draw_region_with_tag(pe.im, r, colors[ii])
        ii += 1

    r1 = d.get_item(0,0)
    print("area = {}".format(compute_region_area(r1)))
    draw_region_with_tag(pe.im, r1, colors[0])
    r2 = d.get_item(1,0)
    print("area = {}".format(compute_region_area(r2)))
    draw_region_with_tag(pe.im, r2, colors[1])
    inter_area = intersect_area(r1, r2)
    draw_region(pe.im, inter_area, colors[4])
    print("inter_area = {}".format(compute_region_area(inter_area)))

    #draw_region_with_tag(pe.im, d.get_item(1,1))
    #print(r1[0])
    print("area (0,1).0 = {}".format(area(r1[0])))
    #print(r1[1])
    #print("area (0,1).1 = {}".format(area(list(r1[1]))))
    #print(r1[2])
    #print("area (0,1).2 = {}".format(area(r1[2])))
    #l2 = [[ 328. , 131.],[ 295. ,187.5],[ 350.58578644 , 220.],[ 384. , 164.5 ]]
    #print(area(list(l2)))
      
    i = 1
    r3, j = find_surpported_region_in_layer(d, r1, i, -6)
    print("({}, {})".format(i, j))

    draw_region_with_tag(pe.im, r3, colors[3], 2)
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)   