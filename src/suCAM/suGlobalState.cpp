#include "suGlobalState.h"

class suGlobalState::AppData
{
public:
	AppData(){}
	~AppData() { clear(); }
	void clear();

};
void suGlobalState::AppData::clear()
{
}


///class suGlobalState
suGlobalState* suGlobalState::p_gOnly = 0;
suGlobalState::suGlobalState()
{
	debugstream.sink(suDebugSinkConsole::sOnly);

	clear();
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
	selected_face_list.clear();
	boundary_face_list.clear();
	load_face_list.clear();
	bSelect_Mode = false;

	if (!pData_) delete pData_;
}

