/**
 * lora-multiboot — Entry for ESP32 / SX1262 multi-slot bootloader
 * Runs two firmwares simultaneously via progressive provisioning.
 */
#include "multiboot.h"
#include <stdio.h>

int main(void) {
    multiboot_init();
    // Load dual-run: Meshtastic (slot 2) + MeshCore (slot 3) together
    multiboot_set_dual_run(true);
    // Load radio base (slot 4) as fallback/default
    multiboot_load_slot(SLOT_RADIO);
    uint32_t active = multiboot_get_active_slot();
    printf("lora-multiboot: active=%lu dual=%s slots_ok=%d\n",
           (unsigned long)active,
           (multiboot_get_active_slot() == SLOT_RADIO ? "dual+base" : "multi"),
           (int)(active < MAX_SLOTS));
    return 0;
}
