#ifndef CAILIE_BRANCH_H
#define CAILIE_BRANCH_H

#include <string>
#include <vector>
#include "state.h"

namespace ca {

class Branch {

	private:
		std::vector<State*> History;
		int ParentBranch;
		int ParentId;

	public:
		//Branch();
		//~Branch();
		void save_state(State *state);
		State* set_state(int index);
		bool is_empty();
		void set_parent(int branch,int id);
		int get_parent_branch();
		int get_parent_id();
		bool is_state_last(int index);

};

}
#endif
