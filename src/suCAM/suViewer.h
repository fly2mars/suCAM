#pragma once
#include <igl/opengl/glfw/Viewer.h>
/*
*Inherit a new class from the viewer
*
*/
class suViewer : public igl::opengl::glfw::Viewer
{
public:
	suViewer() :Viewer() {}

	IGL_INLINE bool load_mesh_from_file(
		const std::string & mesh_file_name_string);
	

public:
	Eigen::MatrixXd N;    //normal 
	Eigen::MatrixXi AFF;  //adjacent faces matrix
	Eigen::MatrixXd V;
	Eigen::MatrixXi F;
	Eigen::MatrixXd C;
};