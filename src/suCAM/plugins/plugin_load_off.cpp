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
#include "../../suReadOFF.h"
#include <igl/triangle_triangle_adjacency.h>
////////////////////////////////////////////////////////////////////////////////

namespace igl
{
	namespace viewer
	{
		namespace glfw
		{
			template <typename DerivedV, typename DerivedF, typename DerivedC>
			IGL_INLINE bool readColorOFF(
				const std::string str,
				Eigen::PlainObjectBase<DerivedV>& V,
				Eigen::PlainObjectBase<DerivedF>& F,
				Eigen::PlainObjectBase<DerivedC>& C)
			{
				std::vector<std::vector<double> > vV;
				std::vector<std::vector<double> > vN;
				std::vector<std::vector<int> > vF;
				std::vector<std::vector<double> > vC;
				bool success = igl::SU::readOFF(str, vV, vF, vN, vC);
				if (!success)
				{
					// readOFF(str,vV,vF,vN,vC) should have already printed an error
					// message to stderr
					return false;
				}
				bool V_rect = igl::list_to_matrix(vV, V);
				if (!V_rect)
				{
					// igl::list_to_matrix(vV,V) already printed error message to std err
					return false;
				}
				bool F_rect = igl::list_to_matrix(vF, F);
				if (!F_rect)
				{
					// igl::list_to_matrix(vF,F) already printed error message to std err
					return false;
				}
				bool C_rect = igl::list_to_matrix(vC, C);
				if (!C_rect)
				{
					// igl::list_to_matrix(vF,F) already printed error message to std err
					return false;
				}
				return true;
			}


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

				//check extend filename
				std::string extension = filename.substr(last_dot + 1);

				if (extension != "off")
					if (extension != "OFF")
					{
						return false;
					}

				//use readColorOFF to load V F C and erase repeated vertices	
				Eigen::MatrixXd V;
				Eigen::MatrixXi F;
				if (!readColorOFF(filename, V, F, suGlobalState::gOnly().C))
					return false;

				//center object												
				//V = V.rowwise() - V.colwise().mean();

				viewer->data().set_mesh(V, F);

				viewer->data().compute_normals(); suGlobalState::gOnly().progress = 0.8;
				update();
				viewer->data().uniform_colors(Eigen::Vector3d(51.0 / 255.0, 43.0 / 255.0, 33.3 / 255.0),
					Eigen::Vector3d(255.0 / 255.0, 228.0 / 255.0, 58.0 / 255.0),
					Eigen::Vector3d(255.0 / 255.0, 235.0 / 255.0, 80.0 / 255.0));

				if (viewer->data().V_uv.rows() == 0)
				{
					viewer->data().grid_texture();
				}

				

				viewer->core.align_camera_center(viewer->data().V, viewer->data().F);
				

				igl::triangle_triangle_adjacency(viewer->data().F, suGlobalState::gOnly().TT);

				std::cout << "F.size = " << viewer->data().F.size() << std::endl;  //debug
				std::cout << "TT = \n" << suGlobalState::gOnly().TT.bottomRows(5) << std::endl;  //debug
				std::cout << "F = \n" << viewer->data().F.bottomRows(5) << std::endl;  //debug
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

