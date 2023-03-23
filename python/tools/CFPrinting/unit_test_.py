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

logging.basicConfig(format='[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG)

if __name__ == '__main__':    
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ppl'))    
    from utils import *
    import MinettoSlicer.stlmesh as stlmesh
    import MinettoSlicer.slicer as slicer   
    import MinettoSlicer.glutils as ut    
  
  

class TestClass(unittest.TestCase):  
    
    def load(self, filename):
        try:
            self.mesh = stlmesh.stlmesh(filename)
            self.mesh_min = self.mesh.min_coordinates()[2]
            self.mesh_max = self.mesh.max_coordinates()[2]
        except Exception as e:
            print(e)
            exit()
            
    def load_config(self, filename):
        f = open(filename, "r")    
        str = f.read()
        self.param = json.loads(str)  
        f.close()

    def slice(self, param):
        P = None
        srt   = False
        self.mesh_slicer = slicer.slicer(self.mesh.triangles,P,param['layer_thickness'],srt)
        self.mesh_slicer.incremental_slicing()       
    
    def test1(self): 
        # Load mesh.
        mesh = stlmesh.stlmesh('models/pendant.stl')
        mesh_min = mesh.min_coordinates()[2]
        mesh_max = mesh.max_coordinates()[2]
        
        # Compute slices.
        P = None
        srt   = False
        delta = 1
        mesh_slicer = slicer.slicer(mesh.triangles,P,delta,srt)
        mesh_slicer.incremental_slicing()
       
            
    def test2(self):
        self.load('models/pendant.stl')
        self.load_config('config.json')        
        self.slice(self.param)    
        
 
if __name__ == '__main__':
    unittest.main()