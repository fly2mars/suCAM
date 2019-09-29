import unittest
import numpy as np

import Gcode

def collinear(p1, p2, p3):
    v21 = p1 - p2
    v23 = p3 - p2
    a = np.dot(v21,v23)
    return True

def resample_curve_by_atapt_distance(pts):
    """ 
    Resample a spational curve
    sparse sampling in line
    dense sampling    
    @pts: the input continuous 3d fill path in an Nx3 np.array
    example:
         c = suPath2D.resample_curve_by_atapt_distance( path)     
    """ 
    resample_c = []
    N = len(pts)
    p0 = pts[0]
    p1 = pts[1]
    for i in range(2, N):
        angle = np.dot(p0,p1)
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

class GcodeTestCase (unittest.TestCase):
    def test_gcode_gen(self):
        pts = np.loadtxt('example/test.gcode.txt')
        params = {startEndSubDirectory: 'config/cf3d_start.gcode', startEndSubDirectory: 'config/cf3d_end.gcode'}
        gcode = Gcode(params)
        
        iLayer = 0
        iPoint = 0
        for p in pts:
        return
        
    

def main():
    unittest.main()

if __name__ == '__main__':
    main()



