"""
A test for 3D slicing and global connection.
The procedure contains steps:
- load mesh
- analyze
- slicing
- traversal access
- sort and output a deque which includes boudaries of all connected area
"""
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
    curdir = os.getcwd()     
    if(os.path.isdir(dir)):
        filelist = [ f for f in os.listdir(dir) if f.endswith(ext) ]            
        for f in filelist:
            os.remove(os.path.join(curdir+"/" + dir, f))  
    else:
        os.mkdir(dir)    
    return

    
if __name__ == "__main__":
    # for test
    colors = pathengine.suPath2D.generate_RGB_list(5)
    # for test end
        
    parser = argparse.ArgumentParser(description="Runs RMEC g-code generator.")
    parser.add_argument('--stl-file', dest='stl_file', required=True)
    parser.add_argument('--output-path', dest='output_path', required=False)
    parser.add_argument('--slice-layers', dest='N', required=False)
    args = parser.parse_args()
    
    N = 10
    file_path = ""
    if args.N:
        N = args.N
    if args.stl_file:
        file_path = args.stl_file
    
    ms = mesh.Mesh.from_file(file_path)
    m = modelInfo.ModelInfo(ms)
    m.set_layers(N)
    #m.set_pixel_size(0.11)
    #m.set_image_size()
    
    print(m.get_info())
        
    image_width = 640
    image_height = 480
    
    #remove all files in images
    remove_files("images")  
    curdir = os.getcwd()
    
    out_path = os.path.join(curdir, "images/slice-%d.png")
    
    
    
    real_pixel_size, real_pixel_size, gcode_minx, gcode_miny = stl2pngfunc.stl2png(file_path, N, m.image_width, 
                        m.image_height, out_path,
                        func = lambda i: print("slicing layer {}/{}".format(i+1,N))
                        )
    
    print('Slicing mesh into ' + out_path)
    
    # algorithm   
    dq = deque()
    
    pe = pathengine.pathEngine()   
    
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
    
    def build_interference_matrix(cs, threshold):
        '''
        @threshold is 
        @return
          a relative matrix m, where m[i,j]=1 means that the distance between i and j is 
          too small to collide with extruder
        TODO: not finished
        '''
        n = len(cs)
        M = np.zeros([n,n])
        
        
        return M
    

    #idx = 0
    regions = {}
    slice_img = "images/slice-%d.png"
    for iLayer in range(N):
        img_file = slice_img % iLayer
        regions[iLayer] = get_region_boundary_from_img(img_file, pe, True)
        #resample
        
        
    dq_cs = deque()
    dq_id = deque() # provide index for connected regions in each layer
    
    # for test
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    # for test end
    #init from layer 0
    idx = 0
    for cs in regions[0]:
        dq_cs.append(cs)
        dq_id.append(idx)
        
        for c in cs:
            pathengine.suPath2D.draw_line(np.vstack([c, c[0]]), pe.im, colors[idx],2)
        idx += 1
    
    #algorithm begin
    
    while len(dq) != 0:
        r = dq[0]
        #if !(interference(r):
           #dq.popleft()
           #r = find_closest_in_next_layer(r)
           
        
        
        
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)         