
#include "branch.h"

#include <string>
#include <vector>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace ca;

/*Branch::Branch(){
	History = new vector<State*>;
	parent = 0;
}*/

void Branch::save_state(State *state){
	State *NewState = NULL;
	NewState = new State(*state);
	History.push_back(NewState);
}

State* Branch::set_state(int index){
	return History[index];
}

bool Branch::is_empty(){
	bool result = false;
	if(History.empty()){
		result = true;
	}
	return result;
}

void Branch::set_parent(int parentbranch, int parentid){
	ParentBranch = parentbranch;
	ParentId = parentid;
}

int Branch::get_parent_branch(){
	return ParentBranch;
}

int Branch::get_parent_id(){
	return ParentId;
}
