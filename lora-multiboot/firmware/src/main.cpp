/**
 * Firmware entry — validates everything, listens before sending, then enables RF.
 */
#include <Arduino.h>
#include "multiboot.h"
#include "scheduler.h"
#include "radio_arbiter.h"
#include "SX1262Router.hpp"

int main(void) {
    multiboot_init();
    SX1262Router_init();

    // Concurrent dual-run setup
    multiboot_set_dual_run(true);
    multiboot_load_concurrent(SLOT_MESHTASTIC);
    multiboot_load_concurrent(SLOT_MESHCORE);

    // Gate: nothing transmits until validation passes AND airwaves are free
    bool gate = SX1262Router_gate();
    bool can_tx = SX1262Router_can_tx();

    if (!gate || !can_tx) {
        return 1;
    }
    multiboot_load_slot(SLOT_RADIO);
    printf("lora-multiboot: validated=%d can_tx=%d concurrent=%d\n",
           (int)gate, (int)can_tx,
           (int)multiboot_active_concurrent_count());
    return 0;
}
