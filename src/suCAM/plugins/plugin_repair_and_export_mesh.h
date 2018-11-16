#pragma once
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/ViewerPlugin.h>
#include <iostream>
#include <igl/unproject_onto_mesh.h>
#include <igl/triangle_triangle_adjacency.h>
#include "../suGlobalState.h"
#include <igl/list_to_matrix.h>

namespace igl
{
	namespace viewer
	{
		namespace glfw 
		{
			class plugin_repair_and_export : public igl::opengl::glfw::ViewerPlugin
			{
			public:
				IGL_INLINE  plugin_repair_and_export() 
				{
					plugin_name = "plugin_repair_and_export";
				}
	
				IGL_INLINE virtual bool key_down(int key, int modifiers);
					

				//internal func
				typedef std::vector<Eigen::DenseIndex> Face;
				typedef std::vector<Face>              Faces;
				typedef std::vector<double>            Vert;
				typedef std::vector<double>            Color;
				typedef std::vector<Vert>              Verts;
				std::map<int, Faces> Fs;
				bool segment_mesh(Eigen::MatrixXd &label_matrix, Eigen::MatrixXi &F, Eigen::MatrixXd V);

			};
		}
		
	}
}

#ifndef IGL_STATIC_LIBRARY
#  include "plugin_repair_and_export_mesh.cpp"
#endif