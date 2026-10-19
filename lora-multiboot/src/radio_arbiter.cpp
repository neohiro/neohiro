#include "radio_arbiter.h"

static uint32_t s_granted_slot = 0xFFFFFFFF;
static uint32_t s_granted_until = 0;
static uint8_t  s_granted_prio = 0;  // priority of granted slot

void arbiter_init(void) {
    s_granted_slot = 0xFFFFFFFF;
    s_granted_until = 0;
    s_granted_prio = 0;
}

bool arbiter_request(uint32_t slot_id, uint32_t slice_ms, uint8_t prio) {
    // Priority arbitration: critical (255) preempts low (0)
    if (s_granted_slot == 0xFFFFFFFF) {
        s_granted_slot = slot_id;
        s_granted_until = slice_ms;
        s_granted_prio = prio;
        return true;
    }
    if (s_granted_slot == slot_id) {
        s_granted_until = slice_ms;
        return true;
    }
    if (prio > s_granted_prio) {
        // Preempt lower-priority transmission
        s_granted_slot = slot_id;
        s_granted_until = slice_ms;
        s_granted_prio = prio;
        return true;
    }
    return false;
}

void arbiter_release(uint32_t slot_id) {
    if (s_granted_slot == slot_id) {
        s_granted_slot = 0xFFFFFFFF;
        s_granted_until = 0;
        s_granted_prio = 0;
    }
}

bool arbiter_is_granted(uint32_t slot_id) {
    return (s_granted_slot == slot_id);
}
