#include "suGlobalState.h"

class suGlobalState::AppData
{
public:
	AppData(){}
	~AppData() { clear(); }
	void clear();

public:


};
void suGlobalState::AppData::clear()
{
}


///class suGlobalState
suGlobalState* suGlobalState::p_gOnly = 0;
suGlobalState::suGlobalState()
{
	debugstream.sink(suDebugSinkConsole::sOnly);

	object_labels.push_back("box");
	object_labels.push_back("ball");
	surface_labels.push_back("Plane");
	surface_labels.push_back("Surface");
	cur_index_of_object_label = 0;
	cur_index_of_surface_label = 0;

	max_angle_between_face_normal = 20;
	max_curvature_between_face = 1;
	clear();

	predfined_colors.resize(20, 3);
	predfined_colors << 255, 179, 0,  //vivid_yellow
		128, 62, 117, //strong_purple
		255, 104, 0,  //vivid_orange 
		166, 189, 215,//very_light_blue
		193, 0, 32,   //vivid_red
		206, 162, 98, //grayish_yellow
		129, 112, 102,//medium_gray
		//these aren't good for people with defective color vision:
		0, 125, 52,   //vivid_green
		246, 118, 142,//strong_purplish_pink
		0, 83, 138,   //strong_blue
		255, 122, 92, //strong_yellowish_pink
		83, 55, 122,  //strong_violet
		255, 142, 0,  //vivid_orange_yellow
		179, 40, 81,  //strong_purplish_red
		244, 200, 0,  //vivid_greenish_yellow
		127, 24, 13,  //strong_reddish_brown
		147, 170, 0,  //vivid_yellowish_green
		89, 51, 21,   //deep_yellowish_brown
		241, 58, 19,  //vivid_reddish_orange
		35, 44, 22;   //dark_olive_green

	predfined_colors = predfined_colors / 255;
}
suGlobalState & suGlobalState::gOnly()
{
	// TODO: insert return statement here
	if (!p_gOnly) {
		p_gOnly = new suGlobalState();
		return *p_gOnly;
	}
	return *p_gOnly;
}

void suGlobalState::release()
{
	clear();
	delete p_gOnly;
	p_gOnly = 0;	
}



void suGlobalState::clear()
{
	bSelect_Mode = false;
	progress = 0;

	if (!pData_) delete pData_;
}

void suGlobalState::clear_selection()
{
	label_matrix.setConstant(-1);
}

