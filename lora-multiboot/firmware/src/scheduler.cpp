#include "scheduler.h"
#include <string.h>
#include "radio_arbiter.h"

static concurrent_task_t s_tasks[MAX_CONCURRENT];
static uint32_t s_tick = 0;

/* A slot's priority follows the role it was provisioned with: the two
 * live frameworks are repeaters and must preempt anything else, the radio
 * slot is normal, and an unrecognised slot stays low so it never blocks
 * a real one. See docs/PRIORITY.md. */
static uint8_t priority_for_slot(uint32_t slot_id) {
    const slot_config_t* s = multiboot_slot_info(slot_id);
    if (s == NULL) return PRIORITY_LOW;
    if (s->role_mask & (ROLE_MESHTASTIC | ROLE_MESHCORE | ROLE_REPEATER)) {
        return PRIORITY_CRITICAL;
    }
    if (s->role_mask & ROLE_RADIO) return PRIORITY_NORMAL;
    return PRIORITY_LOW;
}

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
            s_tasks[i].priority = priority_for_slot(slot_id);
            return true;
        }
    }
    return false;
}

bool scheduler_stop_slot(uint32_t slot_id) {
    for (int i = 0; i < MAX_CONCURRENT; ++i) {
        if (s_tasks[i].running && s_tasks[i].slot_id == slot_id) {
            s_tasks[i].running = false;
            /* A slot that is no longer running must not keep the radio. */
            arbiter_release(slot_id);
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
                /* The slot's turn is up. Ask the arbiter for the radio and
                 * hold it for the slice; the arbiter hands it back on its
                 * own when the slice elapses, and a higher-priority slot
                 * can take it over in the meantime. */
                (void)arbiter_request(s_tasks[i].slot_id, s_tasks[i].slice_ms,
                                      s_tasks[i].priority);
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
