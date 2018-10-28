#pragma once
/*suGlobalState: a singleton class to store global info
 *\note this is a c++ 11 singleton, still need to test
 *\author Yuan Yao
 *\date  2016-07-08
 */
#include <Engines/Utility/debugStream.h>
#include <Eigen/Core>
#include <Eigen/Geometry>
#include <set>
#include <vector>
#include <igl/opengl/glfw/Viewer.h>

class suGlobalState {
public:
	suGlobalState();
	~suGlobalState() { clear(); }
	static suGlobalState& gOnly();
	void release();

	// forbid copy & move
	suGlobalState(const suGlobalState&) = delete;
	suGlobalState& operator = (const suGlobalState&) = delete;
	suGlobalState(suGlobalState&&) = delete;
	suGlobalState& operator =(suGlobalState&&) = delete;

	void clear();
	template<typename T>
	void suGlobalState::log(T msg)
	{
		cdebug << msg << std::endl;
	}

	void set_viewer(igl::opengl::glfw::Viewer *p_viewer) { viewer = p_viewer; }

	//selection
	void clear_selection();

public:
	//AppData operation

	//Parameters for selection
	bool bSelect_Mode;
	std::vector<std::string> object_labels;
	std::vector<std::string> surface_labels;
	int cur_index_of_object_label;
	int cur_index_of_surface_label;
	float max_angle_between_face_normal;
	float max_curvature_between_face;

	Eigen::MatrixXd TT;
	Eigen::MatrixXd label_matrix;

	//UI
	float progress;
	igl::opengl::glfw::Viewer *viewer;
	Eigen::MatrixXd predfined_colors;

public:
	static suGlobalState *p_gOnly;

	

private:

	//by using Pimpl method
	class AppData;
	AppData *pData_;
};