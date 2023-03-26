#!/usr/bin/python3
# run: 
#     python test_show_slice.py models/short.stl -d 0.8

import sys
import os
import argparse
from ctypes import c_void_p
import numpy as np
import math
import OpenGL.GL as gl
import OpenGL.GLUT as glut


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ppl'))    
import MinettoSlicer.stlmesh as stlmesh
import MinettoSlicer.slicer as slicer   
import MinettoSlicer.glutils as ut


## Screen width.
win_width  = 800
## Screen height.
win_height = 600

## Shaders for drawing the mesh and the planes.
program      = None
## Shaders for drawing the contours.
program2     = None
## Vertex array for the mesh.
VAO_mesh     = None
## Vertex buffer for the mesh.
VBO_mesh     = None
## Vertex array for the planes.
VAO_planes   = None
## Vertex buffer for the planes.
VBO_planes   = None
## Vertex array for the segments/contours.
VAO_segments = None
## Vertex buffer for the segments/contours.
VBO_segments = None

## Auxiliar to track mouse x movement.
lastX = win_width/2.0
## Auxiliar to track mouse y movement.
lastY = win_height/2.0
## To check when mouse is clicked.
firstMouse = True

## Set camera position.
camPosition = np.array([0.0, 0.0, -5.0], dtype='float32')
## Set camera target position.
camTarget = np.array([0.0, 0.0, 0.0], dtype='float32')
## Set camera up.
camUp = np.array([0.0, 1.0, 0.0], dtype='float32')
## Set field of view.
fov = 45.0

## Set light color.
lightColor    = np.array([1.0, 1.0, 1.0], dtype='float32')
## Set light position.
lightPosition = np.array([0.0, 0.0, -10.0], dtype='float32')

## STL file name.
stl_file = None
## Number of vertices to be drawn in mesh.
num_vertices_mesh = 0
## Set mesh color.
meshColor = np.array([0.8, 0.8, 0.8, 0.3], dtype='float32')

## Displacement for planes.
delta = None

## Number of vertices to be drawn in planes.
num_vertices_planes = 0
## Set planes color.
planeColor = np.array([1.0, 1.0, 0.0, 0.1], dtype='float32')

## Number of vertices to be drawn in segments/contours.
num_vertices_segments = 0

## Flag to draw mesh.
show_mesh     = True
## Flag to draw planes.
show_planes   = False
## Flag to draw segments.
show_segments = True
## Normalize object to view cube.
view_max =  1.0
## Normalize object to view cube.
view_min = -1.0
## Set model matrix.
model = ut.matRotateX(math.radians(-90.0))

## Mesh and planes vertex shader.
mesh_vs = ""


def parse_input():
    global stl_file
    global delta

    parser = argparse.ArgumentParser(description='Visualize slicer. User can toggle visualized objects using keyboard keys: m for mesh, p for planes and s for segments.')
    parser.add_argument(dest='stl', metavar='STL', help='STL file.')
    parser.add_argument('-d', dest='delta', metavar='delta', type=float, default=2.0, help='Define the displacement between planes.')
    args = parser.parse_args()

    if not(os.path.isfile(args.stl)):
        print ("File " + args.stl + " does not exist.")
        sys.exit()

    stl_file = args.stl
    delta = args.delta

## Main.
#
# Main function.
def main():
    parse_input()

    # Load mesh.
    mesh = stlmesh.stlmesh(stl_file)
    mesh_min = mesh.min_coordinates()[2]
    mesh_max = mesh.max_coordinates()[2]

    # Compute slices.
    P = None
    srt   = False
    mesh_slicer = slicer.slicer(mesh.triangles,P,delta,srt)
    mesh_slicer.incremental_slicing()

if __name__ == '__main__':
    main()
