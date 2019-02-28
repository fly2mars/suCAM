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
    c1s = rs[i][j]
    c1 = []
    
    for c in c1s:
        c1 = c1 + c
    
    is_interfere = False
    
    for ind in range(len(rs)):
        c2 = []
        if ind == j:
            continue
        for c in rs[ind]:
            c2 = c2 + c        
        dist = scid.cdist(c1, c2, 'euclidean')
        min_dist = np.min(dist)
        if min_dist < thresh:
            return True

    return False

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
    def size(self):
        return len(self.d)
        
        
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
    # for test end
    #init from layer 0
    #idx = 0
    #for cs in regions[0]:
        #dq_cs.append(cs)
        #dq_id.append(idx)

        #for c in cs:
            #pathengine.suPath2D.draw_line(np.vstack([c, c[0]]), pe.im, colors[idx],2)
        #idx += 1

    #algorithm begin

    S = []  #sequence
    while d.size() != 0:
        r,i,j = d.get_end()        
        if not is_interference(r,i,j,50):
            #d.remove(i,j)
            S.append(r)
            i = i + 1
            #r = d.find_nearest_region(i, i-1, r)
        else:
            r_next, i_next, j_next = d.get_end(1)  # 1 means the second item
            if i > i_next:
                r = r_next
            



    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)         