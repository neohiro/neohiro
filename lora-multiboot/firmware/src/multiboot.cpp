#include "multiboot.h"
#include <string.h>
#include "scheduler.h"
#include "radio_arbiter.h"

/* Immutable geometry: role -> flash range. Never mutated at runtime. */
const slot_config_t g_slots[MAX_SLOTS] = {
    { SLOT_REPEATER_A, 0x000000, SLOT_SIZE, "Repeater-A", ROLE_REPEATER,    true },
    { SLOT_REPEATER_B, 0x100000, SLOT_SIZE, "Repeater-B", ROLE_REPEATER,    true },
    { SLOT_MESHTASTIC, 0x200000, SLOT_SIZE, "Meshtastic", ROLE_MESHTASTIC,  true },
    { SLOT_MESHCORE,   0x300000, SLOT_SIZE, "MeshCore",   ROLE_MESHCORE,    true },
    { SLOT_RADIO,      0x400000, SLOT_SIZE, "Radio",      ROLE_RADIO,       true },
};

/* Total flash covered by the slot table. A slot that would exceed this
 * budget is refused at init instead of being written at runtime. */
#define SLOT_TABLE_END 0x500000UL

static uint32_t   s_usable_mask = 0;   /* bit per slot */
static uint32_t   s_active_slot = SLOT_RADIO;
static bool       s_dual_run = false;
static slot_writer_fn s_writer = NULL;

void multiboot_set_writer(slot_writer_fn writer) {
    s_writer = writer;
}

void multiboot_init(void) {
    s_usable_mask = 0;
    for (uint32_t i = 0; i < MAX_SLOTS; ++i) {
        const slot_config_t* s = &g_slots[i];
        if (s->size == 0 || s->size > SLOT_SIZE) continue;
        if (s->offset > SLOT_TABLE_END) continue;
        if (s->offset + s->size > SLOT_TABLE_END) continue;  /* overrun refused */
        s_usable_mask |= (1UL << i);
    }
    s_active_slot = SLOT_RADIO;
    s_dual_run = false;
    scheduler_init();
    arbiter_init();
}

bool multiboot_slot_usable(uint32_t slot_id) {
    if (slot_id >= MAX_SLOTS) return false;
    return (s_usable_mask & (1UL << slot_id)) != 0;
}

const slot_config_t* multiboot_slot_info(uint32_t slot_id) {
    if (slot_id >= MAX_SLOTS) return NULL;
    return &g_slots[slot_id];
}

bool multiboot_load_slot(uint32_t slot_id) {
    if (!multiboot_slot_usable(slot_id)) return false;
    s_active_slot = slot_id;
    return true;
}

bool multiboot_update_slot(uint32_t slot_id, const uint8_t* data, uint32_t len) {
    if (!multiboot_slot_usable(slot_id)) return false;
    if (data == NULL || len == 0 || len > SLOT_SIZE) return false;
    if (s_writer == NULL) return false;  /* no backend: refuse, never fake success */
    const slot_config_t* s = &g_slots[slot_id];
    if (s->offset + len > s->offset + s->size) return false;  /* stay inside slot */
    return s_writer(s->offset, data, len);
}

uint32_t multiboot_get_active_slot(void) {
    return s_active_slot;
}

void multiboot_set_dual_run(bool enable) {
    if (enable) {
        s_dual_run = multiboot_slot_usable(SLOT_MESHTASTIC) &&
                     multiboot_slot_usable(SLOT_MESHCORE);
    } else {
        s_dual_run = false;
    }
}

bool multiboot_dual_run_enabled(void) {
    return s_dual_run;
}

bool multiboot_load_concurrent(uint32_t slot_id) {
    if (!multiboot_slot_usable(slot_id)) return false;
    return scheduler_start_slot(slot_id, 10);
}

uint32_t multiboot_active_concurrent_count(void) {
    return scheduler_active_count();
}
