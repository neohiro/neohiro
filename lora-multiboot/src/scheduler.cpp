#include "scheduler.h"
#include <string.h>

static concurrent_task_t s_tasks[MAX_CONCURRENT];
static uint32_t s_tick = 0;

void scheduler_init(void) {
    memset(s_tasks, 0, sizeof(s_tasks));
    s_tick = 0;
}

bool scheduler_start_slot(uint32_t slot_id, uint32_t slice_ms) {
    if (slot_id >= MAX_SLOTS) return false;
    if (scheduler_active_count() >= MAX_CONCURRENT) return false;
    for (int i = 0; i < MAX_CONCURRENT; ++i) {
        if (!s_tasks[i].running) {
            s_tasks[i].slot_id = slot_id;
            s_tasks[i].running = true;
            s_tasks[i].slice_ms = (slice_ms > 0 ? slice_ms : 10);
            s_tasks[i].last_run_ms = s_tick;
            return true;
        }
    }
    return false;
}

bool scheduler_stop_slot(uint32_t slot_id) {
    for (int i = 0; i < MAX_CONCURRENT; ++i) {
        if (s_tasks[i].running && s_tasks[i].slot_id == slot_id) {
            s_tasks[i].running = false;
            return true;
        }
    }
    return false;
}

void scheduler_tick(void) {
    s_tick++;
    // Performance: iterate over running slots; bitmask used for fast active count
    for (int i = 0; i < MAX_CONCURRENT; ++i) {
        if (s_tasks[i].running) {
            if ((s_tick - s_tasks[i].last_run_ms) >= s_tasks[i].slice_ms) {
                s_tasks[i].last_run_ms = s_tick;
                // Concurrent execution: arbitration / context-switch here
            }
        }
    }
}

uint32_t scheduler_active_count(void) {
    // Performance: bitmask + portable count instead of per-element loop
    uint32_t mask = 0;
    for (int i = 0; i < MAX_CONCURRENT; ++i) if (s_tasks[i].running) mask |= (1u << i);
    uint32_t c = 0;
    for (int b = 0; b < 4; ++b) if (mask & (1u << b)) c++;
    return c;
}
