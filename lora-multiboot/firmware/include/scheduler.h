/*
 * Concurrent scheduler — dual/quadboot task runner for lora-multiboot
 * Assumption: ESP32 FreeRTOS or cooperative loop; one radio, multiple stacks
 */
#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stdint.h>
#include <stdbool.h>
#include "multiboot.h"

#define MAX_CONCURRENT 4  // quadboot max

typedef struct {
    uint32_t slot_id;
    bool     running;
    uint32_t last_run_ms;
    uint32_t slice_ms;
    uint8_t  priority;  /* 0=low, 255=critical (repeater/room); arbitration order */
} concurrent_task_t;

void scheduler_init(void);
bool scheduler_start_slot(uint32_t slot_id, uint32_t slice_ms);
bool scheduler_stop_slot(uint32_t slot_id);
void scheduler_tick(void); // call regularly (cooperative loop)
uint32_t scheduler_active_count(void);

#endif
