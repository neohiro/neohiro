/*
 * Relay — cross-protocol decode and slot arbitration
 * One SX1262 = one PHY; relay uses time-division via radio_arbiter.
 */
#ifndef RELAY_H
#define RELAY_H
#include <stdint.h>
#include <stdbool.h>
#include "shared_context_opt.hpp"
void relay_init(void);
bool relay_tick(shared_context_t* ctx);
#endif
