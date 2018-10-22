#include "config.h"
#include <igl/readOBJ.h>
#include <igl/readOFF.h>
#include <igl/per_face_normals.h>
#define DEBUG_TMP
#ifndef DEBUG_TMP
//#include <igl/opengl/glfw/Viewer.h>
#include "suViewer.h"
//#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
//#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
//#include <imgui/imgui.h>
#include <igl/jet.h>
#include "plugin_selection.h"
#include "plugin_menu.h"
#endif

#define MODEL_PATH "data/"

/*
*TestUnit Example
*Compute volume of the input triangle mesha
*Use method from "A symbolic method for calculating the integral properties of arbitrary nonconvex polyhedra"
*/
Eigen::MatrixXd V;
Eigen::MatrixXi F;
std::string filename = MODEL_PATH + std::string("cow.off");


UTFUNC(TestHere)
{
	std::cout << "This is the initial version of suCAM!\n";
	Eigen::MatrixXd m(2, 2);
	m(0, 0) = 3;
	m(1, 0) = 2.5;
	m(0, 1) = -1;
	m(1, 1) = m(1, 0) + m(0, 1);
	Eigen::MatrixXd v(1, 2);
	v << 1, 2;
	std::cout << m << std::endl;
	std::cout << v.transpose() << std::endl;

	std::cout << m * v.transpose() << std::endl;
	std::cout << (m * v.transpose()) << std::endl;
	/*Eigen::MatrixXd alpha = (m * v.transpose()).array().cos() / 
	std::cout << (m * v.transpose()).array().cos() << std::endl;
	std::cout << (m * v.transpose()).array().acos() << std::endl;*/
}
/*Test algorithm of triangle selection with "select and propagation"  
*/
UTFUNC(suCAM)
{
#ifndef DEBUG_TMP
	

	suViewer viewer;
	igl::viewer::glfw::plugin_selection  plugin_selection;
	// Attach a menu plugin
	igl::opengl::glfw::imgui::Plugin_Menu menu;
	viewer.plugins.push_back(&menu);
	viewer.plugins.push_back(&plugin_selection);
	

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
