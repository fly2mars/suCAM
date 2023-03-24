# -*- coding: utf-8 -*-
"""
"""
import copy
import numpy as np
import sys
import os
import argparse
import numpy as np
import json

import logging
import unittest

import VtkAdaptor  # for visulization

logging.basicConfig(format='[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG)

# include ppl
if __name__ == '__main__':    
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ppl'))    
    from utils import *
    import MinettoSlicer.stlmesh as stlmesh
    import MinettoSlicer.slicer as slicer   
    import MinettoSlicer.glutils as ut    
    import modelInfo
    import pathengine
    import mkspiral    

class Polyline(object):
    """
    Encapsulate numpy.array([n,2]) to vtk polyline for visulization
    --------------------------------------------
     def drawPolyline(self, polyline):
        src = vtk.vtkLineSource()
        points = vtk.vtkPoints()
        for i in range(polyline.count()):
            pt = polyline.points[i]
            points.InsertNextPoint((pt.x, pt.y, pt.z))
        src.SetPoints(points)
        return self.drawPdSrc(src)    
    -------------------------------------------
    """
    def __init__(self, path_arr):
        self.data = path_arr
        self.points = []
        for i in range(path_arr.shape[0]):
            p = Polyline.Point3D()
            p.x = path_arr[i,0]
            p.y = path_arr[i,1]
            p.z = 0
            self.points.append(p)
        
    def count(self):
        return self.data.shape[0]
    
    # create a 1st Inner class
    class Point3D:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
 
        
    
class Pipeline(object):
    '''
    Construct a [STL reading, slicing, path plane, gcode generation] pipeline.
    '''
    def __init__(self):
        #self.mesh_info = modelInfo.ModelInfo()
        self.mesh   = None
        self.param  = None
        self.slicer = None        
        
    def load(self, filename):
        try:
            self.mesh = stlmesh.stlmesh(filename)
            self.mesh_min = self.mesh.min_coordinates()[2]
            self.mesh_max = self.mesh.max_coordinates()[2]
        except Exception as e:
            print(e)
            exit()
            
    def load_config(self, config_filename=None):
        config_file = str(config_filename) if config_filename is not None else 'config.json'
        f = open(config_file, "r")    
        str = f.read()
        self.param = json.loads(str)
        f.close()
            
    def slice(self):
        P     = None
        srt   = False
        delta = self.param['layer_thickness']
        
        self.slicer = slicer.slicer(self.mesh.triangles, P, delta, srt)
        self.slicer.incremental_slicing()      
        # export contours to polygon graph
        
    def get_plane(self, idx = 0):
        """
        @return get idx_th plane
        """
        return self.slicer.planes[idx]
    
    def path_plan(self, param):
        self.path_verts = mkspiral.gen_continuous_path_from_slices(self.slicer, collision_dist_xy= 30, collision_dist_z= 3000, offset = -4)
    
    @unimplemented
    def gen_gcode(self, param):
        pass
  
    
    def export(self, output_filename):
        np.savetxt(output_filename, self.path_verts, fmt='%.4f')   
        print('Path file {} is generated'.format(output_filename))
        
    def show(self, path):
        va = VtkAdaptor.VtkAdaptor()        
        pl = Polyline(path)
        va.drawPolyline(pl).GetProperty().SetColor(0, 1, 0)
        va.display()        
        
        
  

class TestClass(unittest.TestCase):  
    def setUp(self):
        self.config_file = 'config.json'
        self.mesh_file   = 'models/short.stl'        
            
    
    # @unittest.skip("just skip")     
    def test1(self): 
        offset = -1
        pl = Pipeline()
        pl.load(self.mesh_file)
        pl.load_config()
        pl.slice()
        pe = pathengine.pathEngine()
        plane = pl.get_plane(0)
        # group_contour = mkspiral.get_region_boundary_from_slice(pe, plane)
        contour_tree = pe.convert_plane_to_PyPolyTree(plane)
        group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')        
        
        #for cs in group_boundary.values():
            #pe.iso_contours_of_a_region.clear()
            #iso_contours = pe.fill_closed_region_with_iso_contours(cs, offset)       
            
        spiral = []
        for boundary in group_boundary.values():
            spiral = mkspiral.spiral(pe, boundary, offset)
            
        pl.show(spiral)  
        
       
            
    def test2(self):
        logging.info("test2-----")           

        
 
if __name__ == '__main__':
    unittest.main()