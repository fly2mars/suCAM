import sys
import os
import argparse
import numpy as np

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ppl'))    
           
import stl2pngfunc
import modelInfo
import pathengine
import mkspiral

tmp_dir = 'r:/images'   # temp dir for saving sliced images

def help_info():
    info = 'python genCP.py [[--in] <stl file>] [[--out] <path file>]\n'  \
           '                [[--first_layer_thickness] <float number>]\n' \
           '                [[--layer_thickness] <float number>]\n'\
           '                [[--infill_offset] <float number>]\n'\
           '                [[--collision_thx] <float number>]\n'
    print(info)
    
def clear_dir(tmp_dir):
    if(os.path.isdir(tmp_dir)):            
        filelist = [f for f in os.listdir(tmp_dir) if f.endswith(".png")]  
        for f in filelist:
            os.remove(os.path.join(tmp_dir, f))    

class ContinuousPathPlanning(object):
    def __init__(self):
        self.mesh_info = modelInfo.ModelInfo()
        
    def load(self, filename):
        try:
            self.mesh_info.load(filename)    
        except Exception as e:
            print(e)
            exit()
    
    def gen_path(self, first_layer_thickness, layer_thickness, infill_offset, collision_thx = 50, tmp_dir = tmp_dir):
        '''
        collisiion_thx: collision threshold in x-y plane, e.g. the default is 500mm
        '''
        self.mesh_info.first_layer_thicknes = first_layer_thickness
        self.mesh_info.layer_thickness = layer_thickness    
        ## Prepare a tmp image path
        curdir = os.getcwd()
        if(not os.path.isdir(tmp_dir)):            
            tmp_dir = os.path.join(curdir, "tmp_images")
            if(not os.path.isdir(tmp_dir)):               
                os.mkdir(tmp_dir) 
                
        ## Convert mm to pixels
        infill_offset = -1 / self.mesh_info.pixel_size   
        collision_thx = collision_thx / self.mesh_info.pixel_size        
        
        self.path_verts = mkspiral.gen_continuous_path(self.mesh_info, tmp_dir, collision_thx, infill_offset)

    
    def export(self, output_filename):
        np.savetxt(output_filename, self.path_verts, fmt='%.4f')   
        print('Path file {} is generated'.format(output_filename))
        



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A multi agenter toplogy optimizer.")
    parser.add_argument('--h', dest='help', action='store_true')
    parser.add_argument('--in', dest='input_file', required=False)
    parser.add_argument('--out', dest='output_file', required=False)
    parser.add_argument('--first_layer_thickness', dest='first_layer_thickness', required=False)
    parser.add_argument('--layer_thickness', dest='layer_thickness', required=False)
    parser.add_argument('--infill_offset', dest='infill_offset', required=False)
    parser.add_argument('--collision_thx', dest='collision_dist', required=False)

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
    first_layer_thickness = float(args.first_layer_thickness) if args.first_layer_thickness else 0.2
    layer_thickness = float(args.layer_thickness) if args.layer_thickness else 0.3
    infill_offset = float(args.infill_offset) if args.infill_offset else 0.4      # Should be converted to pixels
    collision_dist = float(args.collision_dist) if args.collision_dist else 50

    cp = ContinuousPathPlanning()
    cp.load(input_file)
    cp.gen_path(first_layer_thickness, layer_thickness, infill_offset)
    
    cp.export(out_file)
    



