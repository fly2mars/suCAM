#pragma once
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/ViewerPlugin.h>
#include <iostream>
#include <igl/unproject_onto_mesh.h>
#include <igl/triangle_triangle_adjacency.h>
#include "suGlobalState.h"

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
	
				IGL_INLINE virtual bool key_down(int key, int modifiers)
				{
					if (key == 'O')
					{
						//1. segment V, F, C into V_i, F_i and C_i
						//std::cout << "Processing " << viewer->
						std::cout << "Run repair and export ..." << std::endl;
					}
					return false;
				
				}
					
				
				
			public:
				bool b_select_mode;
				Eigen::MatrixXd C;
			};
		}
		
	}
}