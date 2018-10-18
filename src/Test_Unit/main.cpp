#include "config.h"
#include <igl/readOBJ.h>
#include <igl/readOFF.h>
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
#include <imgui/imgui.h>
#include <igl/jet.h>

#define MODEL_PATH "data/"

/*
*TestUnit Example
*Compute volume of the input triangle mesh
*Use method from "A symbolic method for calculating the integral properties of arbitrary nonconvex polyhedra"
*/
Eigen::MatrixXd V;
Eigen::MatrixXi F;
std::string filename = MODEL_PATH + std::string("cow.off");

UTFUNC(ComputeVolume)
{
	return;
	debugstream.sink(suDebugSinkConsole::sOnly);
	cdebug << "ComputeVolume\n----------------------" << std::endl;

	double volume = 0;
	igl::readOFF(filename, V, F);
	auto SignedVolumeOfTriangle = [](Eigen::VectorXd p1,
		Eigen::VectorXd p2,
		Eigen::VectorXd p3) {
		double v321 = p3(0)*p2(1)*p1(2);
		double v231 = p2(0)*p3(1)*p1(2);
		double v312 = p3(0)*p1(1)*p2(2);
		double v132 = p1(0)*p3(1)*p2(2);
		double v213 = p2(0)*p1(1)*p3(2);
		double v123 = p1(0)*p2(1)*p3(2);
		return (1.0f / 6.0f)*(-v321 + v231 + v312 - v132 - v213 + v123);
	};

	
	
	for (int i = 0; i < F.rows(); i++) {
		volume += SignedVolumeOfTriangle(V.row(F(i,0)), V.row(F(i,1)), V.row(F(i,2)));
		//std::cout << volume << std::endl;
	}
	

	std::cout << "Volume = " << fabs(volume) << std::endl;

}
UTFUNC(Eigen)
{
	/*suDebugSinkFile::sOnly.setFile("r:/debug.txt");
	debugstream.sink(suDebugSinkFile::sOnly);
	*/
	return;
	igl::readOFF(filename, V, F);
	cdebug << "Test IO and data\n-------------------" << std::endl;
	igl::readOFF(filename, V, F);
	std::cout << V.bottomRows(5)<< std::endl;
	for (int i = 0; i < 3; i++) {
		std::cout << V.row(0)(i) << std::endl;
	}
}
UTFUNC(draw_multiple_object)
{
	return;
	//It seems that Some obj files have no normal info.
	igl::opengl::glfw::Viewer viewer;
	
	const auto names =
	{ "cube.obj","sphere.obj","xcylinder.obj","ycylinder.obj","zcylinder.obj" };
	std::map<int, Eigen::RowVector3d> colors;
	int last_selected = -1;

	for (auto name : names)
	{
		viewer.load_mesh_from_file(MODEL_PATH + std::string(name));
		colors.emplace(viewer.data().id, 0.5*Eigen::RowVector3d::Random().array() + 0.5);
	}
	

	viewer.callback_key_down = [&](igl::opengl::glfw::Viewer& viewer, unsigned char key, int mod)
	{
		printf("%d\n", key);
		if (key == '1')
		{
			int old_id = viewer.data().id;
			if (viewer.erase_mesh(viewer.selected_data_index))
			{
				colors.erase(old_id);
				last_selected = -1;
			}
			return true;
		}
		return false;
	};
	

	// Refresh selected mesh colors
	viewer.callback_pre_draw =
		[&](igl::opengl::glfw::Viewer &)
	{
		if (last_selected != viewer.selected_data_index)
		{
			for (auto &data : viewer.data_list)
			{
				data.set_colors(colors[data.id]);
			}
			viewer.data_list[viewer.selected_data_index].set_colors(Eigen::RowVector3d(0.9, 0.1, 0.1));
			last_selected = viewer.selected_data_index;
		}
		return false;
	};
	viewer.launch();
	
}

UTFUNC(make_color_edge_point_and_label)
{
	Eigen::MatrixXd C;
	igl::readOFF(MODEL_PATH "cow.off", V, F);

	// Plot the mesh
	igl::opengl::glfw::Viewer viewer;
	// Attach a menu plugin
	igl::opengl::glfw::imgui::ImGuiMenu menu;
	viewer.plugins.push_back(&menu);

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
}

int main(int argc, char* argv[])
{
	bool state = suUnitTest::gOnly().run ();
	suUnitTest::gOnly().dumpResults (std::cout);

	return state;
}
