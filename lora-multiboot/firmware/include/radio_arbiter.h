/*
 * SX1262 Radio Arbiter — time-division arbitration for concurrent slots
 * Critical limitation: one SX1262 = one PHY config at a time; true RF
 * simultaneous is physically impossible. This layer enforces time-division.
 */
#ifndef RADIO_ARBITER_H
#define RADIO_ARBITER_H

#include <stdint.h>
#include <stdbool.h>

#define PRIORITY_LOW      0
#define PRIORITY_NORMAL  128
#define PRIORITY_CRITICAL 255

void arbiter_init(void);
// Request radio for a slot; returns true if granted for slice_ms
bool arbiter_request(uint32_t slot_id, uint32_t slice_ms, uint8_t prio);
void arbiter_release(uint32_t slot_id);
bool arbiter_is_granted(uint32_t slot_id);
// Tick-based expiry: call regularly (e.g., from loop / scheduler_tick)
void arbiter_tick(void);

#endif
