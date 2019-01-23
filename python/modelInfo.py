import math
import numpy as np
import stl
from stl import mesh

'''
A class for holding the infomation of mesh
Default unit is milimeter
'''

class ModelInfo():
    def __init__(self, mesh = None):
        if (mesh != None):
            self.mesh = mesh
            self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz = self.find_mins_maxs()
        else:
            self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz  = 0,0,0,0,0,0
        self.set_pixel_size(0.1)
        self.set_image_size()
        self.gcode_minx = 0       # for record minx and miny from slice result
        self.gcode_miny = 0
        
        self.first_layer_thickness = 0.35
        self.layer_thickness = 0.5
        
        return
    
        
    def get_info(self):
        info = '''
               Bounding box: ([{}, {}, {}], [{}, {}, {}])
               Image size ({}, {})
               Pixel size: {}
               Slice layers: {}
               First layer thickness: {}
               Layer thickness: {}
               Real pixel size: [{}, {}]
               Start position: [{}, {}]
               '''
        info = info.format(self.minx, self.miny, self.minz, self.maxx, self.maxy, self.maxz, 
                    self.image_width, self.image_height, 
                    self.get_pixel_size(), self.get_layers(), self.first_layer_thickness, self.layer_thickness,
                    self.real_pixel_size_x, self.real_pixel_size_y, self.gcode_minx, self.gcode_miny)
        
        return info
    
    def set_layers(self, nLayers):
        height = self.maxz - self.minz
        self.layer_thickness = height / nLayers
        self.first_layer_thickness = self.layer_thickness 
        
        
    def set_image_size(self):
        w = self.maxx - self.minx
        h = self.maxy - self.miny
        
        self.image_width  = int(w / self.pixel_size)
        self.image_height = int(h / self.pixel_size)
        
    def set_pixel_size(self, pix_size = 0.05):
        #default 1 pixel = 0.01 mm 
        self.pixel_size = pix_size
        self.real_pixel_size_x = self.pixel_size
        self.real_pixel_size_y = self.pixel_size
        
        
    def get_pixel_size(self):        
        return self.pixel_size
    
    def get_layers(self):        
        nlayers = math.ceil(((self.maxz - self.minz) - self.first_layer_thickness ) / self.layer_thickness )  + 1
        return nlayers
        
    def find_mins_maxs(self):
        minx = maxx = miny = maxy = minz = maxz = None
        for p in self.mesh.points:
            # p contains (x, y, z)
            if minx is None:
                minx = p[stl.Dimension.X]
                maxx = p[stl.Dimension.X]
                miny = p[stl.Dimension.Y]
                maxy = p[stl.Dimension.Y]
                minz = p[stl.Dimension.Z]
                maxz = p[stl.Dimension.Z]
            else:
                maxx = max(p[stl.Dimension.X], maxx)
                minx = min(p[stl.Dimension.X], minx)
                maxy = max(p[stl.Dimension.Y], maxy)
                miny = min(p[stl.Dimension.Y], miny)
                maxz = max(p[stl.Dimension.Z], maxz)
                minz = min(p[stl.Dimension.Z], minz)
        return minx, maxx, miny, maxy, minz, maxz    
    
    
if __name__ == '__main__':
    ms = mesh.Mesh.from_file("e:/data/stl/barobox.stl")
    m = ModelInfo(ms)
    print(m.get_info())