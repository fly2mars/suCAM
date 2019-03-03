"""
A test for 3D slicing and global connection.
The procedure contains steps:
- load mesh
- analyze
- slicing
- traversal access
- sort and output a deque which includes boudaries of all connected area
example:
   ex4 --stl-file frameguide.stl --output-path images  --slice-layers 5
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
        #resample
        for i in range(len(cs_region)):
            cs_region[i] = pathengine.suPath2D.resample_curve_by_equal_dist(cs_region[i], 4) 
        cs_region_list.append(cs_region)
    return cs_region_list

def is_interference(rs, i, j, thresh):
    '''
    @rs is regions in the i-th layer
    @i current id of layer
    @j current id of region 
    @thresh is a distance threshold
    
    @return
      True:  interference 
      False: not interference 
    '''
    is_interfere = False
    
    if idx in 
    pid_c1, pid_c2, min_dist = get_min_dist(b1, b2)
    
    
    
   
        dist = scid.cdist(c1, c2, 'euclidean')
        min_dist = np.min(dist)
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
            cs = cs + b[idx]
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
    def get_end(self):
        r = self.d[0]
        i = self.di[0]
        j = self.dj[0]
        return r, i, j
    def remove_end(self):
        self.d.popleft()
        self.di.popleft()
        self.dj.popleft()
        return
    def pop_end(self):
        r, i, j = self.get_end()
        self.remove_end()
        return
    def get_item(self, i, j):
        """
        Return r
        If r(i,j) is not found, return R[0]
        """
        for idx in range(len(self.di)):
            if (self.di[idx] == i) and (self.dj[idx] == j ):
                return self.d[idx]
        return self.d[0]
    
    def remove_item(self, i, j):
        for idx in range(len(self.di)):
            if (self.di[idx] == i) and (self.dj[idx] == j ):
                self.di.remove(i)
                self.dj.remove(j)
                del self.d[idx]
        return
    def find_nearest_region_in_with_layer_id(self, r, k):
        """
        Given a r(i,j), find the nearest r(k,?)
        """
        min_d = float("inf")

        j = -1
        b1 = r
        r_idx = -1
        for idx in range(len(self.di)):            
            ii = self.di[idx] 
            if ii == k:         
                jj = self.dj[idx]
                b2 = self.get_item(ii, jj)
                d = get_min_dist(b1, b2)
                if d < min_d:
                    j = jj
                    min_d = d
                    r_idx = idx
        return self.d[r_idx], j
                
                
    def size(self):
        return len(self.d)



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

    out_path = os.path.join(output_path, "/slice-%d.png")


    real_pixel_size, real_pixel_size, gcode_minx, gcode_miny = stl2pngfunc.stl2png(file_path, N, m.image_width, 
                        m.image_height, out_path,
                        func = lambda i: print("slicing layer {}/{}".format(i+1,N))
                        )

    print('Slicing mesh into ' + out_path)

    # algorithm   
    pe = pathengine.pathEngine()       
    
    #R = {r_ij}
    R = []
    #slice_img = "images/slice-%d.png"
    for i in range(N):
        img_file = out_path % i
        rs = get_region_boundary_from_img(img_file, pe, True)
        R.append(rs)   #
        
    #d = di = dj = deque()    
    d = RDqueue(R)
    #get total num of r_ij
    #total_N = 0    
    #for i in range(len(R)):
        #for j in range(len(R[i])):
            #d.append(R[i][j])
            #di.append(i)
            #dj.append(j) 
            #total_N += 1
            
    print("There are {} regions".format(d.size()))
    #d = deque(R)    

    # for test
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
   
    #algorithm: 3D printing sequence
    S = []  #sequence
    dist_th = 50
    r,i,j = d.get_end() 
    
    while d.size() != 0:           
        if not is_interference(r,i,j,dist_th):            
            S.append(r)
            i = i + 1
            r, j = d.find_nearest_region_in_with_layer_id(r, i+1)
        else:
            r_next, i_next, j_next = d.get_end()  # 1 means the second item
            if i <= i_next:                       # The new region is not lower than current, 
                S.append(r)                       # so the nozzle doesn't have to go down. 
                d.remove_item(i,j)
            r = r_next
            i = i_next
            j = j_next            


    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)         