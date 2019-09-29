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
        self.mesh = mesh
        if (mesh != None):            
            self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz = self.find_mins_maxs()
        else:
            self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz  = 0,0,0,0,0,0
        
        self.path = ""
        self.border_size = 0.5      # mm
        self.set_pixel_size(0.1)  # pixel
        self.set_image_size()
        self.gcode_minx = 0       # for record minx and miny from slice result
        self.gcode_miny = 0
        
        self.first_layer_thickness = 0.3
        self.layer_thickness = 0.2
        self.z_list = []  # z list for each layer        
        
        return
    
    def load(self, file_path):
        self.mesh = mesh.Mesh.from_file(file_path)
        if self.mesh == None:
            return
        self.path = file_path
        self.minx, self.maxx, self.miny, self.maxy, self.minz, self.maxz = self.find_mins_maxs()
        self.init(self.pixel_size, self.first_layer_thickness, self.layer_thickness)
        return self.mesh
    def init(self, pixel_size, first_layer_thickness, layer_thickness):
        if self.mesh == None:
            return
        self.set_pixel_size(pixel_size)
        self.first_layer_thickness = first_layer_thickness
        self.layer_thickness = layer_thickness
        self.set_image_size()
        
    def get_info(self):
        info = '''
               Bounding box: ([{}, {}, {}], [{}, {}, {}])
               Image size ({}, {})
               Border size: {} pixels
               Pixel size: {}
               Slice layers: {}
               First layer thickness: {}
               Layer thickness: {}
               Real pixel size: [{}, {}]
               Slice z list: {}
               Start position: [{}, {}]
               '''
        info = info.format(self.minx, self.miny, self.minz, self.maxx, self.maxy, self.maxz, 
                    self.image_width, self.image_height, 
                    self.border_size / self.pixel_size,
                    self.get_pixel_size(), 
                    self.get_layers(), 
                    self.first_layer_thickness, self.layer_thickness,
                    self.real_pixel_size_x, self.real_pixel_size_y,
                    self.get_z_list(),
                    self.gcode_minx, self.gcode_miny)
        
        return info
    
    def set_layers(self, nLayers):
        
        height = self.maxz - self.minz
        self.layer_thickness = height / nLayers
        self.first_layer_thickness = self.layer_thickness 
        
        
    def set_image_size(self):
        w = self.maxx - self.minx + self.border_size
        h = self.maxy - self.miny + self.border_size
        
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
        '''
        Compute & Check if layer height is suitable
        I rewrite this to generate a z_list, which can be used in slicer directly
        '''  
        if self.maxz < 0.00001:
            return 0, []
        self.z_list.clear()
        # layer 0
        if self.first_layer_thickness < self.maxz:
            self.z_list.append(self.first_layer_thickness)
        
        # layer 0
        z = self.z_list[0]
        # layer 1..n
        top_slice_z_limit = self.maxz - self.layer_thickness / 2.1    #not 2, to avoid precision problem
        
        while True:
            z += self.layer_thickness
            if z <= top_slice_z_limit:
                self.z_list.append(z)
            else:
                break
        # top layer
        if z <= self.maxz + self.layer_thickness / 1.9:
            last_slice_pos = self.maxz - self.layer_thickness / 4
            self.z_list.append(last_slice_pos)
            
        nlayers = len(self.z_list)  # math.ceil(((self.maxz - self.minz) - self.first_layer_thickness ) / self.layer_thickness )  + 1
        return nlayers
    
    def get_z_list(self):
        return np.round(self.z_list, 3)
    
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
    m_info = ModelInfo()
    print(m_info.get_info())
    
    ms = mesh.Mesh.from_file("c:/data/bunny-flatfoot.stl")
    m_info = ModelInfo(ms)
    m_info.first_layer_thickness = 0.3
    m_info.layer_thickness = 0.2    
    print(m_info.get_info())
    