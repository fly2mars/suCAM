#include "config.h"
#include <igl/readOBJ.h>
#include <igl/readOFF.h>
#include <igl/per_face_normals.h>
//#define DEBUG_TMP
#ifndef DEBUG_TMP
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
#include <imgui/imgui.h>
#include <igl/jet.h>
#include "plugin_selection.h"
#endif

#define MODEL_PATH "data/"

/*
*TestUnit Example
*Compute volume of the input triangle mesh
*Use method from "A symbolic method for calculating the integral properties of arbitrary nonconvex polyhedra"
*/
Eigen::MatrixXd V;
Eigen::MatrixXi F;
std::string filename = MODEL_PATH + std::string("cow.off");
UTFUNC(TestHere)
{
	std::cout << "This is the initial version of suCAM!\n";
}
/*Test algorithm of triangle selection with "select and propagation"  
*/
UTFUNC(suCAM)
{
#ifndef DEBUG_TMP
	Eigen::MatrixXd C;
	igl::readOFF(MODEL_PATH "cow.off", V, F);

	// Plot the mesh
	igl::opengl::glfw::Viewer viewer;  
	igl::viewer::glfw::plugin_selection  plugin_selection;
	// Attach a menu plugin
	igl::opengl::glfw::imgui::ImGuiMenu menu;
	viewer.plugins.push_back(&menu);
	viewer.plugins.push_back(&plugin_selection);

	viewer.data().set_mesh(V, F);

	// Find the bounding box
	Eigen::Vector3d m = V.colwise().minCoeff();
	Eigen::Vector3d M = V.colwise().maxCoeff();

	// Corners of the bounding box
	Eigen::MatrixXd V_box(8, 3);
	V_box <<
		m(0), m(1), m(2),
		M(0), m(1), m(2),
		M(0), M(1), m(2),
		m(0), M(1), m(2),
		m(0), m(1), M(2),
		M(0), m(1), M(2),
		M(0), M(1), M(2),
		m(0), M(1), M(2);

	// Edges of the bounding box
	Eigen::MatrixXi E_box(12, 2);
	E_box <<
		0, 1,
		1, 2,
		2, 3,
		3, 0,
		4, 5,
		5, 6,
		6, 7,
		7, 4,
		0, 4,
		1, 5,
		2, 6,
		7, 3;

	// Plot the corners of the bounding box as points
	viewer.data().add_points(V_box, Eigen::RowVector3d(1, 0, 0));

	// Plot the edges of the bounding box
	for (unsigned i = 0; i < E_box.rows(); ++i)
	{
		viewer.data().add_edges
		(
			V_box.row(E_box(i, 0)),
			V_box.row(E_box(i, 1)),
			Eigen::RowVector3d(1, 0, 0)
		);
		// Add label
		Eigen::VectorXd P = (V_box.row(E_box(i,0)) + V_box.row(E_box(i,1))) / 2;
		viewer.data().add_label(P, std::to_string(i));
	}
		
	std::stringstream l1;
	l1 << m(0) << ", " << m(1) << ", " << m(2);
	viewer.data().add_label(m, l1.str());
	std::stringstream l2;
	l2 << M(0) << ", " << M(1) << ", " << M(2);
	viewer.data().add_label(M, l2.str());

	// Use the z coordinate as a scalar field over the surface
	Eigen::VectorXd Z = V.col(2);

	// Compute per-vertex colors
	igl::jet(Z, true, C);

	// Add per-vertex colors
	viewer.data().set_colors(C);

	// Launch the viewer
	viewer.launch();
#endif
}

int main(int argc, char* argv[])
{
	bool state = suUnitTest::gOnly().run ();
	suUnitTest::gOnly().dumpResults (std::cout);

	return state;
}
