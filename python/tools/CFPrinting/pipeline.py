import sys
import os
import argparse
import numpy as np
import json

import logging
logging.basicConfig(format='[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG)

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ppl'))    
    from utils import *
    import MinettoSlicer.stlmesh as stlmesh
    import MinettoSlicer.slicer as slicer    
    # import stl2pngfunc
    # import modelInfo
    # import pathengine
    # import mkspiral 
           


tmp_dir = 'r:/images'   # temp dir for saving sliced images

def help_info():
    info = 'python pipeline.py [[--in] <stl file>] [[--out] <path file>]\n'  \
           '                [[--config] <config file name>]\n'\
           ' eg: python pipeline_genGCode  --in models/part1.stl  --config config.json'
           
    print(info)
    
def clear_dir(tmp_dir):
    if(os.path.isdir(tmp_dir)):            
        filelist = [f for f in os.listdir(tmp_dir) if f.endswith(".png")]  
        for f in filelist:
            os.remove(os.path.join(tmp_dir, f))    

class Pipeline(object):
    '''
    Construct a [STL reading, slicing, path plane, gcode generation] pipeline.
    '''
    def __init__(self):
        #self.mesh_info = modelInfo.ModelInfo()
        self.mesh = None
        pass
        
    def load(self, filename):
        try:
            self.mesh = stlmesh.stlmesh(filename)
            self.mesh_min = self.mesh.min_coordinates()[2]
            self.mesh_max = self.mesh.max_coordinates()[2]
        except Exception as e:
            print(e)
            exit()
            
    def slice(self, param):
        P = None
        srt   = False
        self.mesh_slicer = slicer.slicer(self.mesh.triangles,P,param['layer_thickness'],srt)
        self.mesh_slicer.incremental_slicing()           
    
    @unimplemented
    def path_plan(self, param):
        pass
    
    @unimplemented
    def gen_gcode(self, param):
        pass
        
    
    
    def gen_path(self, first_layer_thickness, layer_thickness, infill_offset, collision_thxy = 50, collision_thz = 50, tmp_dir = tmp_dir):
        '''
        collisiion_thx: collision threshold in x-y plane, e.g. the default is 500mm
       
        self.mesh_info.first_layer_thickness = first_layer_thickness
        self.mesh_info.layer_thickness = layer_thickness    
        
        ## Prepare a tmp image path
        curdir = os.getcwd()
        if(not os.path.isdir(tmp_dir)):            
            tmp_dir = os.path.join(curdir, "tmp_images")
            if(not os.path.isdir(tmp_dir)):               
                os.mkdir(tmp_dir) 
                
        ## Convert mm to pixels
        infill_offset = -1 * infill_offset / self.mesh_info.pixel_size   
        collision_thxy = collision_thxy / self.mesh_info.pixel_size  
        collision_thz = collision_thz / self.mesh_info.pixel_size  
        
        self.path_verts = mkspiral.gen_continuous_path_with_constraint(self.mesh_info, tmp_dir, collision_thxy, collision_thz, infill_offset)
        '''
        pass

    
    def export(self, output_filename):
        np.savetxt(output_filename, self.path_verts, fmt='%.4f')   
        print('Path file {} is generated'.format(output_filename))
        



if __name__ == '__main__':  
    
    parser = argparse.ArgumentParser(description="A multi agenter toplogy optimizer.")
    parser.add_argument('--h', dest='help', action='store_true')
    parser.add_argument('--in', dest='input_file', required=False)
    parser.add_argument('--out', dest='output_file', required=False)
    parser.add_argument('--config', dest='config_file', required=False)    

    args = parser.parse_args()
    if args.help:
        help_info()
        exit()

    input_file = ""
    if args.input_file:
        input_file = str(args.input_file)
    else:
        print("error:argument --in: expected one argument")
        help_info()

    out_file = str(args.output_file) if args.output_file else os.path.splitext(input_file)[0] + '.path'
    
    ## load config    
    config_file = str(args.config_file) if args.output_file else 'config.json'
    f = open(config_file, "r")    
    str = f.read()
    fab_config = json.loads(str)
    
    first_layer_thickness = fab_config['first_layer_thickness']
    layer_thickness = fab_config['layer_thickness']
    infill_offset = fab_config['infill_offset']
    collision_distxy = fab_config['collision_distxy']
    collision_distz = fab_config['collision_distz']

    cp = Pipeline()
    cp.load(input_file)
    #cp.gen_path(first_layer_thickness, layer_thickness, infill_offset, collision_distxy, collision_distz)
    
    #cp.export(out_file)
    cp.slice(fab_config)
    cp.path_plan(fab_config)
    cp.gen_gcode(fab_config)
    



