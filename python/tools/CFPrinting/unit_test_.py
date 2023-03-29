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
import random

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
        if(type(path_arr) == list):
            path_arr = np.array(path_arr)
        for i in range(path_arr.shape[0]):
            p = Polyline.Point3D()
            p.x = path_arr[i,0]
            p.y = path_arr[i,1]
            p.z = 0
            self.points.append(p)
        
    def count(self):
        return len(self.data)#.shape[0]
    
    # create a Inner class for Point
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
        self.va = VtkAdaptor.VtkAdaptor()   
        
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
        
        with open(config_file, 'r') as f:
            self.param = json.load(f)
            
    def slice(self):
        """
        Slice by Minetto's slicer
        Hold info in the slicer
        """
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
    
    @unimplemented
    def fill_layer(self, idx = 0, path_type=0):
        """
        @return path of one layer
        @idx is layer index. Here the IO is 
        @path_type = ISO_CONTOUR, FERMAT_SPIRAL ...
        """
        pass

    @unimplemented
    def optimize_one_layer(self, path):
        """
        @path input path, only from a closed region
        @return optimized path
        """
        pass

    
    def path_plan(self, param):
        self.path_verts = mkspiral.gen_continuous_path_from_slices(self.slicer, collision_dist_xy= 30, collision_dist_z= 3000, offset = -4)
    
    @unimplemented
    def gen_gcode(self, param):
        pass
  
    
    def export_path(self, output_filename):
        np.savetxt(output_filename, self.path_verts, fmt='%.4f')   
        print('Path file {} is generated'.format(output_filename))

    @unimplemented
    def export_gcode(self):
        pass
        
    def add_polyline_to_scene(self, path, color=(1, 0, 0)):
        pl = Polyline(path)
        self.va.drawPolyline(pl).GetProperty().SetColor(color)
            
    @unimplemented
    def run(self):
        """
        Running a slicing-path planning-gcode generation process.
        """        
        pass     
    
    @unimplemented
    def run_web_server(self):
        """
        Running a web server as user interface
        """
        pass

    def show(self):
        self.va.display()

    from enum import Enum
    class PathType(Enum):
        ISO_CONTOUR   = 0
        FERMAT_SPIRAL = 1

    
        
  

class TestClass(unittest.TestCase):  
    def setUp(self):
        self.config_file = 'config.json'
        self.mesh_file   = 'models/part1.stl'        
            
    #@unittest.skip("just skip")     
    def test_fill_with_pathEngine(self):         
        logging.info("test: test_fill_with_pathEngine-----")
        offset = 0.4
        pl = Pipeline()
        pl.load(self.mesh_file)
        pl.load_config()       # load slice config file
        pl.slice()
        path = pl.fill_layer(0, pl.PathType.ISO_CONTOUR)
        path = pl.fill_layer(0, pl.PathType.FERMAT_SPIRAL)
        pl.optimize_one_layer(path)
        # pl.show()
        pass
    
    @unittest.skip("just skip")     
    def test_fill_isocontours_in_onelayer(self): 
        """
        Filling iso contours with contours[i][j], where i is inner order, j is contour index. 
        """
        logging.info("test1: test_fill_isocontours_in_onelayer-----")
        offset = 0.4
        pl = Pipeline()
        pl.load(self.mesh_file)
        pl.load_config()       # load slice config file
        pl.slice()
        
        
        pe = pathengine.pathEngine()
        plane = pl.get_plane(0)  # get layer 0
        
        contour_tree = pe.convert_plane_to_PyPolyTree(plane)
        #pl.show(contour_tree.Childs[0].Contour)
        group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')        
                
        for cs in group_boundary.values():       
            #print(np.int16(cs))
            # add outter contour
            pe.iso_contours_of_a_region.clear()
            iso_contours = pe.fill_closed_region_with_iso_contours(cs, offset) 
            
            
            for i in range(len(iso_contours)):
                for j in range(len(iso_contours[i])):
                    c = np.concatenate((iso_contours[i][j], np.array([iso_contours[i][j][0]])), axis=0)
                    pl.add_polyline_to_scene(c)            
            for c in cs:
                c = np.concatenate((c, np.array([c[0]])), axis=0)
                pl.add_polyline_to_scene(c, (0,0,1))            
                
        pl.show()
       
            
    @unittest.skip("just skip")     
    def test_fill_continuousFS_in_onelayer(self): 
        logging.info("test2: test_fill_continuousFS_in_onelayer-----")  
        """
        Filling continuous Fermat's Spiral with contours[i][j], where i is inner order, j is contour index. 
        """
        offset = 0.4
        pl = Pipeline()
        pl.load(self.mesh_file)
        pl.load_config()
        pl.slice()
        
        #pl.pathplan()
        #pl.optimize() # 
        #pl.gen_gcode()
        pe = pathengine.pathEngine()
        plane = pl.get_plane(0)
        
        contour_tree = pe.convert_plane_to_PyPolyTree(plane)
        #pl.show(contour_tree.Childs[0].Contour)
        group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')  
        
        #################################
        # Generate N color list
        #################################
        def generate_RGB_list(N):
            import colorsys
            HSV_tuples = [(x*1.0/N, 0.8, 0.9) for x in range(N)]
            RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
            rgb_list = tuple(RGB_tuples)
            return np.array(rgb_list) * 255   
        N = 50
        colors = generate_RGB_list(N)        
        
        spiral = []
        # group_contour = mkspiral.get_region_boundary_from_slice(pe, plane)
        for boundary in group_boundary.values():
            for c in boundary:
                pl.add_polyline_to_scene(c, (1,0,1))
                
            pe.iso_contours_of_a_region.clear()
            iso_contours = pe.fill_closed_region_with_iso_contours(boundary, offset)     
            
            # 这里之前使用最近距离建立相邻关系，考虑使用clipper的tree结构建立
            ######################################
            # Generate grpah from isocontour
            ######################################
            #def gen_graph_from_isocontours(iso_contours):
            #    return iso_contours_2D, graph
            iso_contours_2D, graph = pe.init_isocontour_graph(iso_contours)     
            graph.to_Mathematica("")
    
            if not graph.is_connected():
                print("not connected")
                ret = pe.reconnect_from_leaf_node(graph, iso_contours, abs(offset * 1.2))
                if(ret):
                    print("re-connect...")
                    graph.to_Mathematica("")
    
            # generate a minimum-weight spanning tree
            graph.to_reverse_delete_MST()
            graph.to_Mathematica("")
            # generate a minimum-weight spanning tree
            pocket_graph = graph.gen_pockets_graph()
            pocket_graph.to_Mathematica("")
            # generate spiral for each pockets
            # deep first search
            spirals = {}
            pe.dfs_connect_path_from_bottom(0, pocket_graph.nodes, iso_contours_2D, spirals, offset) 
            
            #return spirals[0] 
        
            #spiral = mkspiral.spiral(pe, boundary, offset)
            #spiral = pe.fill_spiral_in_connected_region(boundary, offset)
            spiral = pe.smooth_curve_by_savgol(spirals[0], 5, 1)            
            #pl.add_polyline_to_scene(spirals)        
            #print(type(spirals))
            #print(spirals)
            pl.add_polyline_to_scene(spiral)
                
        
        pl.show()        

        
 
if __name__ == '__main__':
    unittest.main()