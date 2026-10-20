#include "radio_arbiter.h"

static uint32_t s_granted_slot = 0xFFFFFFFF;
static uint32_t s_granted_until = 0;   // slice length, in ticks
static uint32_t s_granted_since = 0;   // tick the current grant started at
static uint8_t  s_granted_prio = 0;  // priority of granted slot
static uint32_t s_tick = 0;

void arbiter_init(void) {
    s_granted_slot = 0xFFFFFFFF;
    s_granted_until = 0;
    s_granted_since = 0;
    s_granted_prio = 0;
    s_tick = 0;
}

bool arbiter_request(uint32_t slot_id, uint32_t slice_ms, uint8_t prio) {
    // Priority arbitration: critical (255) preempts low (0)
    if (s_granted_slot == 0xFFFFFFFF) {
        s_granted_slot = slot_id;
        s_granted_until = slice_ms;
        s_granted_since = s_tick;
        s_granted_prio = prio;
        return true;
    }
    if (s_granted_slot == slot_id) {
        s_granted_until = slice_ms;
        s_granted_since = s_tick;  // re-arm the slice for the holder
        return true;
    }
    if (prio > s_granted_prio) {
        // Preempt lower-priority transmission
        s_granted_slot = slot_id;
        s_granted_until = slice_ms;
        s_granted_since = s_tick;
        s_granted_prio = prio;
        return true;
    }
    return false;
}

void arbiter_release(uint32_t slot_id) {
    if (s_granted_slot == slot_id) {
        s_granted_slot = 0xFFFFFFFF;
        s_granted_until = 0;
        s_granted_since = 0;
        s_granted_prio = 0;
    }
}

bool arbiter_is_granted(uint32_t slot_id) {
    return (s_granted_slot == slot_id);
}

/* A grant is a slice, not a lease: once the slice has elapsed the radio
 * goes back to the pool without anyone having to release it. Without this
 * a holder that never released would keep the radio for good, and the
 * only way out would be preemption by a higher priority slot. */
void arbiter_tick(void) {
    s_tick++;
    if (s_granted_slot == 0xFFFFFFFF) return;
    if ((s_tick - s_granted_since) < s_granted_until) return;
    s_granted_slot = 0xFFFFFFFF;
    s_granted_until = 0;
    s_granted_since = 0;
    s_granted_prio = 0;
}
