#include "suViewer.h"


IGL_INLINE bool suViewer::load_mesh_from_file(
	const std::string & mesh_file_name_string)
{

	// first try to load it with a plugin
	for (unsigned int i = 0; i < plugins.size(); ++i)
	{
		if (plugins[i]->load(mesh_file_name_string))
		{
			return true;
		}
	}
	//
	size_t last_dot = mesh_file_name_string.rfind('.');
	if (last_dot == std::string::npos)
	{
		std::cerr << "Error: No file extension found in " <<
			mesh_file_name_string << std::endl;
		return false;
	}
	std::string extension = mesh_file_name_string.substr(last_dot + 1);

	if (extension == "off" || extension == "OFF")
	{

		if (!igl::readOFF(mesh_file_name_string, V, F))
			return false;
		data().set_mesh(V, F);
		// Use the z coordinate as a scalar field over the surface
		Eigen::VectorXd Z = V.col(2);
		std::cout << Z << std::endl;

		// Compute per-vertex colors
		igl::jet(Z, true, C);

		// Add per-vertex colors
		data().set_colors(C);
	}
	std::cout << "Hi there!\n";
	return true;
}