// This file is part of libigl, a simple c++ geometry processing library.
//
// Copyright (C) 2018 Jérémie Dumas <jeremie.dumas@ens-lyon.org>
//
// This Source Code Form is subject to the terms of the Mozilla Public License
// v. 2.0. If a copy of the MPL was not distributed with this file, You can
// obtain one at http://mozilla.org/MPL/2.0/.
////////////////////////////////////////////////////////////////////////////////
#include "../plugin_menu.h"
#include <igl/project.h>
#include <imgui/imgui.h>
#include <imgui_impl_glfw_gl3.h>
#include <imgui_fonts_droid_sans.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include <array>
#include "../suGlobalState.h"
#include "plugin_load_off.h"
#include <igl/triangle_triangle_adjacency.h>
////////////////////////////////////////////////////////////////////////////////

namespace igl
{
	namespace viewer
	{
		namespace glfw
		{

			IGL_INLINE bool Plugin_Load_Off::load(std::string filename)
			{
				viewer->data().clear();
				size_t last_dot = filename.rfind('.');
				if (last_dot == std::string::npos)
				{
					std::cerr << "Error: No file extension found in " <<
						filename << std::endl;
					return false;
				}

				std::string extension = filename.substr(last_dot + 1);

				if (extension == "off" || extension == "OFF")
				{
					Eigen::MatrixXd V;
					Eigen::MatrixXi F;
					if (!igl::readOFF(filename, V, F))
						return false;
					viewer->data().set_mesh(V, F);    
					
					suGlobalState::gOnly().progress = 0.7; 
					update();

					viewer->data().compute_normals(); suGlobalState::gOnly().progress = 0.8; 
					update();
					viewer->data().uniform_colors(Eigen::Vector3d(51.0 / 255.0, 43.0 / 255.0, 33.3 / 255.0),
						Eigen::Vector3d(255.0 / 255.0, 228.0 / 255.0, 58.0 / 255.0),
						Eigen::Vector3d(255.0 / 255.0, 235.0 / 255.0, 80.0 / 255.0));

					if (viewer->data().V_uv.rows() == 0)
					{
						viewer->data().grid_texture();
					}

					suGlobalState::gOnly().progress = 0.95; 
					update();
					
					viewer->core.align_camera_center(viewer->data().V, viewer->data().F); 
					suGlobalState::gOnly().progress = 1.0; 
					update();
				}

				igl::triangle_triangle_adjacency(viewer->data().F, suGlobalState::gOnly().TT);
				suGlobalState::gOnly().label_matrix.resize(viewer->data().F.rows(), 2);
				suGlobalState::gOnly().label_matrix.setConstant(-1);
				return true;
			}

			void Plugin_Load_Off::update()
			{
				for (int i = 0; i < viewer->plugins.size(); i++)
				{
					
				}
			}

		} // end namespace
	} // end namespace
} // end namespace

