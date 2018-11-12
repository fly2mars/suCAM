#pragma once
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/ViewerPlugin.h>
#include <iostream>
#include <igl/unproject_onto_mesh.h>
#include <igl/triangle_triangle_adjacency.h>
#include "suGlobalState.h"

#define LABEL_COW  999
int gFid = -1;

const double cov2angle = 180 / igl::PI;
double max_angle = 0;

void generate_adjacent_faces_by_vertex(const Eigen::MatrixXi & F,
	const Eigen::MatrixXd & V,
	std::vector<std::set<Eigen::DenseIndex>>& A)
{
	A.clear();
	Eigen::DenseIndex N = F.rows();
	Eigen::DenseIndex M = V.rows();
	A.resize(M);
	std::cout << "faces: " << int(N) << std::endl;
	for (Eigen::DenseIndex i = 0; i < N; i++) {
		for (int j = 0; j < 3; j++) {
			//add relation: F(i) each vertex of F(i) 
			A[F(i, j)].insert(i);
		}
	}
}
template <typename DerivedF>
void generate_adjacent_faces_by_faces(
	const Eigen::PlainObjectBase<DerivedF> &F)
{
	DerivedF TTi;
	igl::triangle_triangle_adjacency(F, TT, TTi);

}


bool should_propagate(int i, int j, int label, Eigen::MatrixXd &N, int j_label)
{
	
	double dot = N.row(i).dot(N.row(j)) / sqrt((N.row(i).norm() * N.row(j).norm()) );
	double angle_between_normal = acos(dot) * cov2angle;
	return angle_between_normal <= max_angle &&
		j_label == -1;
}

typedef std::function<void(int idx)> ProcessCallback;

void propagate_from_neighbor_loop(int cur_face_idx, int label, const ProcessCallback &proc = ProcessCallback())
{
	max_angle = suGlobalState::gOnly().max_angle_between_face_normal;
	Eigen::MatrixXd &TT = suGlobalState::gOnly().TT;
	Eigen::MatrixXd &label_matrix = suGlobalState::gOnly().label_matrix;
	Eigen::MatrixXd &N = suGlobalState::gOnly().viewer->data().F_normals;
	int label_index_in_matrix = -1;
	if (suGlobalState::gOnly().b_label_item[0])   label_index_in_matrix = 0;
	if (suGlobalState::gOnly().b_label_item[1])   label_index_in_matrix = 1;
	
	if (label_index_in_matrix == -1) return;
	std::vector<int> face_list;
	face_list.push_back(cur_face_idx);
	while (!face_list.empty())
	{
		int cur_id = face_list.back();
		proc(cur_id);
		label_matrix(cur_id, label_index_in_matrix) = label;
		face_list.pop_back();
		for (int i = 0; i<3; i++)
		{
			int j = TT(cur_id, i);
			if (j == -1) continue;  //debug
			
			
			
			if (should_propagate(cur_id, j, label, N, label_matrix(j, label_index_in_matrix)))
			{
				face_list.push_back(j);
			}
		}
	}

}

namespace igl
{
	namespace viewer
	{
		namespace glfw 
		{
			class plugin_selection : public igl::opengl::glfw::ViewerPlugin
			{
			public:
				IGL_INLINE  plugin_selection() :b_select_mode(false)
				{
					plugin_name = "plugin_selection";
				}
	
				IGL_INLINE virtual bool key_down(int key, int modifiers)
				{
					if (key == 'C')
					{
						if (suGlobalState::gOnly().C.size() == 0)
						{
							return false;
						}
						viewer->data().set_colors(suGlobalState::gOnly().C);
	
					}
					if (key == 'F') //use face color
					{
						if (suGlobalState::gOnly().C.size() == 0)
						{
							return false;
						}
						Eigen::MatrixXi &F = viewer->data().F;
						Eigen::MatrixXd C = suGlobalState::gOnly().C;
						Eigen::MatrixXd FC;
						int N = F.rows();
						
						FC.resize(N, 3);
	
						for (int i = 0; i < N; i++)
						{
							//use vert(0)'s color for each face
							for (int j = 0; j < 3; j++)
							{
								FC(i, j) = C(F(i, 0), j);
							}
						}
						
						viewer->data().set_colors(FC);
						viewer->data().set_colors(suGlobalState::gOnly().C);

					}
					if (key == 'S')
					{
						b_select_mode = !b_select_mode;
						if (b_select_mode)
						{
							C = Eigen::MatrixXd::Constant(viewer->data().F.rows(), 3, 1);
						}
						else {
							viewer->data().uniform_colors(Eigen::Vector3d(51.0 / 255.0, 43.0 / 255.0, 33.3 / 255.0),
								Eigen::Vector3d(255.0 / 255.0, 228.0 / 255.0, 58.0 / 255.0),
								Eigen::Vector3d(255.0 / 255.0, 235.0 / 255.0, 80.0 / 255.0));
						}
						std::cout << "select mode is " << b_select_mode << std::endl;
						return false;
					}

					if (key == 'E')
					{
						if (b_select_mode)
						{
							std::cout << "Extend selection from face " << gFid << std::endl;
							std::set<Eigen::DenseIndex> Sel_Set;
							//find faces around the face gFid
							std::set<Eigen::DenseIndex> surround_face_set;
							if (gFid != -1)
							{
								std::cout << "Get surround region..\n";
								auto callback_process = [&](int idx) {
									surround_face_set.insert(idx);
								};
								int cur_object_label = suGlobalState::gOnly().get_cur_color_id();
								propagate_from_neighbor_loop(gFid, cur_object_label, callback_process);
							}
							
				
							Sel_Set = surround_face_set;
						
							for (auto i : Sel_Set)
							{
								C.row(i) << suGlobalState::gOnly().predfined_colors.row(suGlobalState::gOnly().cur_index_of_object_label);//1, 0, 0;															
							}
							viewer->data().set_colors(C);
							std::cout << Sel_Set.size() << " faces are processed!\n";
							
						}
					}
					return false;
				}
				IGL_INLINE virtual bool mouse_move(int mouse_x, int mouse_y)
				{
					if (b_select_mode)
					{
						Eigen::Vector3f bc;
						int fid = -1;

						// Cast a ray in the view direction starting from the mouse position
						int y = viewer->core.viewport(3) - mouse_y;

						if (igl::unproject_onto_mesh(Eigen::Vector2f(mouse_x, y), viewer->core.view * viewer->core.model,
							viewer->core.proj, viewer->core.viewport, viewer->data().V, viewer->data().F, fid, bc))
						{
							// hover effect
							Eigen::Vector3d ori_color = C.row(fid);
							C.row(fid) << 1, 0, 0;
										
							viewer->data().set_colors(C);
							C.row(fid) = ori_color;
												
							gFid = fid; //copy to global variable
							return true;
						}
						else { //else set original color
							viewer->data().set_colors(C);
						}
					}
					return false;
				}


				
				IGL_INLINE virtual bool mouse_down(int button, int modifier)
				{
					if (!b_select_mode) return false;

					Eigen::Vector3f bc;
					int fid = -1;
					// Cast a ray in the view direction starting from the mouse position
					double x = viewer->current_mouse_x;
					double y = viewer->core.viewport(3) - viewer->current_mouse_y;

					if (igl::unproject_onto_mesh(Eigen::Vector2f(x, y), viewer->core.view * viewer->core.model,
						viewer->core.proj, viewer->core.viewport, viewer->data().V, viewer->data().F, fid, bc))
					{
						if (button == static_cast<int>(igl::opengl::glfw::Viewer::MouseButton::Left)) {
							// paint hit red
							std::cout << fid << " is selected " << std::endl;
							
							C.row(fid) << 1, 0, 0;

							//Find vox by face id
							//Eigen::Vector3d p(bc(0), bc(1), bc(2));
							//viewer->data().add_label(p, std::string("P"));
							
						}
						else if (button == static_cast<int>(igl::opengl::glfw::Viewer::MouseButton::Right)) {
							suGlobalState::gOnly().clear_selection();
							C = Eigen::MatrixXd::Constant(viewer->data().F.rows(), 3, 1);
							viewer->data().set_colors(C);
							std::cout << " selected faces is cleared " << std::endl;
							
						}
						return false;

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