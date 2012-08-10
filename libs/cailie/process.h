
#ifndef CAILIE_PROCESS_H
#define CAILIE_PROCESS_H

#include <pthread.h>
#include <vector>
#include <set>
#include "messages.h"
#include "net.h"
#include "packing.h"
#ifdef CA_MPI
#include "mpi_requests.h"
#endif

#define CA_RESERVED_PREFIX sizeof(CaTokens)

#define CA_TAG_TOKENS 0
#define CA_TAG_SERVICE 1

enum CaServiceMessageType { CA_SM_QUIT, CA_SM_NET_CREATE, CA_SM_NET_HALT, CA_SM_WAKE , CA_SM_EXIT };
class CaProcess;
class CaThread;
struct CaServiceMessage {
	CaServiceMessageType type;
};

struct CaServiceMessageNetCreate : CaServiceMessage {
	int net_id;
	int def_index;
};

struct CaTokens {
	int place_index;
	int net_id;
	int tokens_count;
};

struct CaUndeliverMessage {
	int net_id;
	void *data;
};

#ifdef CA_SHMEM
class CaPacket {
	public:
	int tag;
	void *data;

	CaPacket *next;
};
#endif

class CaProcess {
	public:
		CaProcess(int process_id, int process_count, int threads_count, int defs_count, CaNetDef **defs);
		virtual ~CaProcess();
		void start();
		void join();
		void start_and_join();
		void clear();
		void inform_new_network(CaNet *net, CaThread *thread);
		void inform_halt_network(CaThread *thread);
		void send_barriers(pthread_barrier_t *barrier1, pthread_barrier_t *barrier2);
		void update_net_id_counters(int net_id);
		bool is_future_id(int net_id);

		int get_threads_count() const { return threads_count; }
		int get_process_count() const { return process_count; }
		int get_process_id() const { return process_id; }
		void write_reports(FILE *out) const;
		void fire_transition(int transition_id, int instance_id);

		void quit_all(CaThread *thread);
		void quit() { quit_flag = true; }
		void halt(CaThread *thread);

		CaNet * spawn_net(CaThread *thread, int def_index, int id, bool globally);

		int new_net_id();

		CaThread *get_thread(int id);

		bool quit_flag;

		void multisend(int target, CaNet * net, int place, int tokens_count, const CaPacker &packer, CaThread *thread);
		void multisend_multicast(const std::vector<int> &targets, CaNet *net, int place, int tokens_count, const CaPacker &packer, CaThread *thread);

		void process_service_message(CaThread *thread, CaServiceMessage *smsg);
		void process_packet(CaThread *thread, int tag, void *data);
		int process_packets(CaThread *thread);

		#ifdef CA_SHMEM
		void add_packet(int tag, void *data);
		#endif

		#ifdef CA_MPI
		void wait();
		#endif

		void broadcast_packet(int tag, void *data, size_t size, CaThread *thread, int exclude = -1);
		void write_header(FILE *file);
	protected:

		void autohalt_check(CaNet *net);

		int process_id;
		int process_count;
		int threads_count;
		int defs_count;
		CaNetDef **defs;
		CaThread *threads;
		int id_counter;
		pthread_mutex_t counter_mutex;
		int *process_id_counter;
		std::vector<void* > too_early_message;
		/*memory of net's id which wasn't created, but was halted*/
		bool net_is_halted;

		#ifdef CA_SHMEM
		pthread_mutex_t packet_mutex;
		CaPacket *packets;
		#endif
};

#endif
