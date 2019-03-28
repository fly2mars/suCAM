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
def draw_line(point_lists, img, color, line_width=1):
    point_lists = point_lists.astype(int)
    pts = point_lists.reshape((-1,1,2))
    cv2.polylines(img, [pts], False, color, thickness=line_width, lineType=cv2.LINE_AA)
    cv2.imshow("Art", img)

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

class RDqueue():
    """
    A deque to hold r(i,j)
    """
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

def find_sequence_test(path):
    return

def calculate_dist_test(r1, r2):

    return

def spiral(boundary,offset):
    
    spiral = pe.fill_spiral_in_connected_region(boundary, offset)        

    spiral = pe.smooth_curve_by_savgol(spiral, 3, 1)
    pathengine.suPath2D.draw_line(spiral, pe.im, [100,255,100],1)      
    
    return spiral
    

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
        for r in rs:
            for c in r:
                print(c.shape)
        R.append(rs) #

    #d = di = dj = deque()    
    d = RDqueue(R)


    print("There are {} regions".format(d.size()))
    #d = deque(R)    

    # for test
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)

    #algorithm: 3D printing sequence
    S = [] #sequence with [[i,j]......]
    dist_th = 20
    r,i,j = d.get_end() 

    while d.size() != 0:  
        #print(len(d))
        #print(S)
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
    
    # A demo
    def draw_region(im, r, color = [255,0,0]):        
        for c in r:
            pathengine.suPath2D.draw_line(np.vstack((c,c[0])), im, color,1)      

    d = RDqueue(R)
    k = 0    
    pe.im = pe.im + 255
    #for [i,j] in S:
        #r = d.get_item(i,j)
        #pe.im = pe.im +255
        #draw_region(pe.im, r, colors[k])
        #cv2.imwrite("E:/images/s" + str(k) + ".png", pe.im)
        #k += 1
        
    start_code=open("configs/A1/start.txt")
    start_data=start_code.read()    
    f=open("R:/sequence.txt","w")
    f.write(start_data)   
    f.write("\n")
    for i in range(0,len(S)-1):
        Z=0.3500
        r=d.get_item(S[i][0],S[i][1])
        cs=spiral(r,-4)
        E=3
        cs=cs/10
        
        if i==0:
            f.write("G1 "+"Z"+str("%0.3f"%Z)+" F7800"+"\n")
            f.write("G1 "+"X"+str("%0.3f"%(cs[0][0]))+" Y"+str("%0.3f"%(cs[0][1])) +" F7800"+"\n") 
        else:
            if S[i][0]<S[i-1][0]:
                Z= Z + S[i][0] * 0.3
                f.write("G1 "+"X"+str("%0.3f"%(cs[0][0]))+" Y"+str("%0.3f"%(cs[0][1])) +" F7800"+"\n")
                f.write("G1 "+"Z"+str("%0.3f"%Z)+" 7800"+"\n")
            elif S[i][0]==S[i-1][0]:
                f.write("G1 "+"X"+str("%0.3f"%(cs[0][0]))+" Y"+str("%0.3f"%(cs[0][1])) +" F7800"+"\n")
            else:
                Z= Z + S[i][0] * 0.3
                f.write("G1 "+"Z"+str("%0.3f"%Z)+" F7800"+"\n")
                f.write("G1 "+"X"+str("%0.3f"%(cs[0][0]))+" Y"+str("%0.3f"%(cs[0][1])) +" F4800"+"\n")                
        f.write("G1 E3.00000 F2400"+"\n")
        for i in range (0,len(cs)-1):
            if i==0:
                f.write("G1 "+"X"+str("%0.3f"%(cs[i][0]))+" Y"+str("%0.3f"%(cs[i][1]))+" E" + str("%0.3f"%E)+" F2400"+"\n")
            else:
                distance=np.linalg.norm(cs[i]-cs[i-1])
                E=distance*0.049890412+E
                f.write("G1 "+"X"+str("%0.3f"%(cs[i][0]))+" Y"+str("%0.3f"%(cs[i][1]))+ " E" + str("%0.3f"%E)+" F2400"+"\n")
        f.write("G92 E0"+"\n")
    end_code=open("configs/A1/end.txt")
    end_data=end_code.read()
    f.write(end_data) 
    f.close
    
    
