/*
 * lora-multiboot — Role-aware multi-slot firmware platform
 * Assumption: single SX1262 serving Meshtastic and MeshCore together
 * with progressive provisioning / non-destructive updates.
 * Slots: 0=Repeater-A, 1=Repeater-B, 2=Meshtastic, 3=MeshCore, 4=Radio
 */
#ifndef MULTIBOOT_H
#define MULTIBOOT_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_SLOTS 5
#define SLOT_SIZE 0x100000  // 1 MiB per slot (ESP32 flash partitioning)

// User-requested role mapping
#define SLOT_REPEATER_A 0
#define SLOT_REPEATER_B 1
#define SLOT_MESHTASTIC 2
#define SLOT_MESHCORE   3
#define SLOT_RADIO      4

// Firmware role flags
#define ROLE_REPEATER    (1 << 0)
#define ROLE_MESHTASTIC  (1 << 1)
#define ROLE_MESHCORE    (1 << 2)
#define ROLE_RADIO       (1 << 3)

typedef struct {
    uint32_t slot_id;
    uint32_t offset;
    uint32_t size;
    char     name[32];
    uint32_t role_mask;
    bool     active;
} slot_config_t;

extern slot_config_t g_slots[MAX_SLOTS];

void multiboot_init(void);
bool multiboot_load_slot(uint32_t slot_id);
bool multiboot_update_slot(uint32_t slot_id, const uint8_t* data, uint32_t len);
uint32_t multiboot_get_active_slot(void);
void multiboot_set_dual_run(bool enable); // Simultaneous Meshtastic + MeshCore

// Concurrent execution support (scheduler + arbiter required)
bool multiboot_load_concurrent(uint32_t slot_id);
uint32_t multiboot_active_concurrent_count(void);

#endif
