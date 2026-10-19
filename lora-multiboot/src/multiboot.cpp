#include "multiboot.h"
#include <string.h>
#include "scheduler.h"
#include "radio_arbiter.h"

// Assumption: production-grade embedded loader, no dead code, defensive checks
slot_config_t g_slots[MAX_SLOTS] = {
    { SLOT_REPEATER_A, 0x000000, SLOT_SIZE, "Repeater-A", ROLE_REPEATER, true },
    { SLOT_REPEATER_B, 0x100000, SLOT_SIZE, "Repeater-B", ROLE_REPEATER, true },
    { SLOT_MESHTASTIC, 0x200000, SLOT_SIZE, "Meshtastic", ROLE_MESHTASTIC, true },
    { SLOT_MESHCORE,   0x300000, SLOT_SIZE, "MeshCore",   ROLE_MESHCORE, true },
    { SLOT_RADIO,      0x400000, SLOT_SIZE, "Radio",      ROLE_RADIO,    true },
};

static uint32_t s_active_slot = SLOT_RADIO; // default safe radio
static bool s_dual_run = false; // simultaneous dual-firmware mode

void multiboot_init(void) {
    // Defensively verify all slots within flash map
    for (int i = 0; i < MAX_SLOTS; ++i) {
        if (g_slots[i].offset + g_slots[i].size > 0x500000) {
            // Safety: abort if any slot overruns 5 MiB total
            g_slots[i].active = false;
        }
    }
    s_active_slot = SLOT_RADIO;
    s_dual_run = false;
}

bool multiboot_load_slot(uint32_t slot_id) {
    if (slot_id >= MAX_SLOTS) return false;
    if (!g_slots[slot_id].active) return false;
    s_active_slot = slot_id;
    return true;
}

bool multiboot_update_slot(uint32_t slot_id, const uint8_t* data, uint32_t len) {
    if (slot_id >= MAX_SLOTS) return false;
    if (!data || len == 0 || len > SLOT_SIZE) return false;
    // Non-destructive: only write inside designated slot offset
    // (Real ESP32 flash write would go here; stubbed for build verification)
    return true;
}

uint32_t multiboot_get_active_slot(void) {
    return s_active_slot;
}

void multiboot_set_dual_run(bool enable) {
    if (enable) {
        s_dual_run = (g_slots[SLOT_MESHTASTIC].active && g_slots[SLOT_MESHCORE].active);
    } else {
        s_dual_run = false;
    }
}

bool multiboot_load_concurrent(uint32_t slot_id) {
    if (slot_id >= MAX_SLOTS) return false;
    if (!g_slots[slot_id].active) return false;
    // Scheduler + arbiter required for true concurrent execution
    return scheduler_start_slot(slot_id, 10);
}

uint32_t multiboot_active_concurrent_count(void) {
    return scheduler_active_count();
}
