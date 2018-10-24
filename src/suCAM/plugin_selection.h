#pragma once
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/ViewerPlugin.h>
#include <iostream>
#include <igl/unproject_onto_mesh.h>
#include <igl/triangle_triangle_adjacency.h>

#define LABEL_COW  999
int gFid = -1;
std::vector<std::set<Eigen::DenseIndex>> AFF;
Eigen::VectorXd TC;    //trangle center 
Eigen::MatrixXd TT;
Eigen::MatrixXd N;
Eigen::MatrixXd label_matrix;

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

void temp_init(const Eigen::MatrixXi & F,
	const Eigen::MatrixXd & V,
    const Eigen::MatrixXd & FN)
{
	generate_adjacent_faces_by_vertex(F, V, AFF);
	generate_adjacent_faces_by_faces(F);
	N = FN;
	label_matrix.resize(F.rows(), 2);   //two lables for each face
	label_matrix.setConstant(-1);
	//compute center coordinate for each triangles
	
}

/*
* Evaluate the simlarity of face i and face j
* sim(i,j, F, V)
* sim = \theta ||p_i - p_j ||_2    + \theta ||cos(n_i,n_j)||
*/
float sim(Eigen::DenseIndex i, Eigen::DenseIndex j, 	
	const Eigen::MatrixXi & F,
	const Eigen::MatrixXd & V,
	const Eigen::MatrixXd & N,
	double theta1 = 0.5, double theta2 = 0.5
	)
{		
	Eigen::Vector3d v1, v2, n1, n2;
	v1 << TC(i, 0), TC(i, 1), TC(i, 2);
	v2 << TC(j, 0), TC(j, 1), TC(j, 2);
	
	float dist = (v1 - v2).norm();
	n1 << N(i, 0), N(i, 1), N(i, 2);
	n2 << N(j, 0), N(j, 1), N(j, 2);
	
	float dangle = 1 - n1.dot(n2) / (n1.norm() * n2.norm());
	dangle /= 2;    //normalize to [0,1)
	float sim = theta1 * dist + theta2 * dangle;
	return sim;
}

bool should_propagate(int i, int j, int label)
{
	//double dist = 
	//const max_diff_mean_curvature = 1.0
	const double max_angle = 30;
	const double cov2angle = 180 / igl::PI;
	double dot = N.row(i).dot(N.row(j)) / sqrt((N.row(i).norm() * N.row(j).norm()) );
	double angle_between_normal = acos(dot) * cov2angle;

	/*std::cout << "\n--\n";
	std::cout << "--" << N.row(i) << " " << N.row(j) << " " << std::endl;
	std::cout << "--" << angle_between_normal << std::endl;*/
	return angle_between_normal <= max_angle && 
		   label != label_matrix(j,0);   //don't deal with labeled triangle
		/*return neibour.label == label &&
		angle_between_normal <= max_angle * dist &&
		diff_mean_curvature <= max_diff_mean_curvature * dist;*/
    
}

typedef std::function<void(int idx)> ProcessCallback;
void propagate_from_neighbor(int &cur_face_idx, int &label, const ProcessCallback &proc = ProcessCallback())
{	
	proc(cur_face_idx);
	label_matrix(cur_face_idx, 0) = label;
	for (int i=0; i<3; i++)
	{
		int j = TT(cur_face_idx, i);
		if (j == -1) continue;  //debug
		if (should_propagate(cur_face_idx, j, label) )
		{
			//std::cout << "propagate to " << j << "\n";
			propagate_from_neighbor(j, label, proc);
		}
	}

}

void propagate_from_neighbor_loop(int cur_face_idx, int label, const ProcessCallback &proc = ProcessCallback())
{
	std::vector<int> face_list;
	face_list.push_back(cur_face_idx);
	while (!face_list.empty())
	{
		int cur_id = face_list.back();
		proc(cur_id);
		label_matrix(cur_id, 0) = label;
		face_list.pop_back();
		for (int i = 0; i<3; i++)
		{
			int j = TT(cur_id, i);
			if (j == -1) continue;  //debug
			if (should_propagate(cur_id, j, label))
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
					if (key == 'S')
					{
						b_select_mode = !b_select_mode;
						if (b_select_mode)
						{
							C = Eigen::MatrixXd::Constant(viewer->data().F.rows(), 3, 1);
							//init AFF
							if (AFF.empty())
							{
								temp_init(viewer->data().F, viewer->data().V, viewer->data().F_normals);
								std::cout << AFF.size() << " faces in AFF init done\n";
								std::cout << TT.rows() << "faces in ATT init done\n";
							}
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
								/*Eigen::MatrixXi &F_ = viewer->data().F;
								for (int ii = 0; ii < 3; ii++)
								{
									int vid = F_(gFid, ii);
									for (auto idx : AFF[vid])
									{
										surround_face_set.insert(idx);
									}
								}			*/
								auto callback_process = [&](int idx) {
									surround_face_set.insert(idx);
								};
								int cur_label = LABEL_COW;
								propagate_from_neighbor_loop(gFid, cur_label, callback_process);
							}
							
							//compare each face i with face gFid(last labeled set)
							    //if  Sim(i, gFid)  > TH 
							    //push i to a set Sel_Set
							Sel_Set = surround_face_set;
							//for each face in Sel_Set
							// hover effect
							C = Eigen::MatrixXd::Constant(viewer->data().F.rows(), 3, 1);
							for (auto i : Sel_Set)
							{
								C.row(i) << 1, 0, 0;
															
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
							for (int j = 0; j < 3; j++)
							{
								//std::cout << TT(fid, j) << std::endl;  //debug
								if (TT(fid, j) == -1) continue;
								C.row(TT(fid, j)) << 1, 0, 0;
							}
							
							viewer->data().set_colors(C);
							C.row(fid) = ori_color;
							for (int j = 0; j < 3; j++)
							{
								if (TT(fid, j) == -1) continue;
								C.row(TT(fid, j)) = ori_color;
							}
							
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