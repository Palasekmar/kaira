
#include <stdio.h>
#include "messages.h"
#include "process.h"

void CaMessageNewUnit::process(CaThread *thread) 
{
	std::vector<CaTransition*> transitions = def->get_transitions();
	std::vector<CaTransition*>::iterator i;
	for (i = transitions.begin(); i != transitions.end(); i++) {
		thread->add_job(new CaJob(unit, *i));
	}
}

void CaMessageBarriers::process(CaThread *thread) 
{
	pthread_barrier_wait(barrier1);
	pthread_barrier_wait(barrier2);
}

void CaMessageLogInit::process(CaThread *thread)
{
	pthread_barrier_wait(barrier1);
	thread->init_log(logname);
	pthread_barrier_wait(barrier2);
	
	if (thread->get_id() == 0) {
		pthread_barrier_destroy(barrier1);
		pthread_barrier_destroy(barrier2);
		delete barrier1;
		delete barrier2;
	}
}
