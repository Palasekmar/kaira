#ifndef CAILIE_LISTENER_H
#define CAILIE_LISTENER_H

#include <pthread.h>
#include <string>
#include <vector>
#include "state.h"
#include "branch.h"

namespace ca {

class Process;

class Listener {
	public:
		Listener() : process_count(0), processes(NULL), listen_socket(0),
			thread(0), start_barrier(NULL), state(NULL){}
		~Listener() {
			cleanup_state();
		}
		void init(int port);
		void wait_for_connection();
		int get_port();

		void start();
		void main();
		void process_commands(FILE *comm_in, FILE *comm_out);

		void set_processes(int process_count, Process **processes) {
			this->process_count = process_count;
			this->processes = processes;
		}

		void set_start_barrier(pthread_barrier_t *barrier) {
			start_barrier = barrier;
		}

	protected:

		void prepare_state();
		void cleanup_state();

		void save_state();
		void set_state(int branch, int index);

		int process_count;
		Process **processes;
		int listen_socket;
		pthread_t thread;
		pthread_barrier_t *start_barrier;
		std::vector<std::string> sequence;
		State *state;

		int CurrentBranch;
		std::vector<Branch*> Branches;

		//std::vector<State*> History;

};

}
#endif
