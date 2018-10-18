#pragma once
/*suGlobalState: a singleton class to store global info
 *\note this is a c++ 11 singleton, still need to test
 *\author Yuan Yao
 *\date  2016-07-08
 */
#include <Engines/Utility/debugStream.h>
#include <set>
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


	static suGlobalState *p_gOnly;

	//app config

	//constraint setting
	//only one force is supported now
	std::set<int> load_face_list;          //for load setting
	std::set<int> boundary_face_list;      //for freedom setting
	std::set<int> selected_face_list;      //list of selected face indexes
	std::set<int> last_selected_face_list; //list of last selected indexes

	//UI
	bool bSelect_Mode;
private:

	//by using Pimpl method
	class AppData;
	AppData *pData_;
};