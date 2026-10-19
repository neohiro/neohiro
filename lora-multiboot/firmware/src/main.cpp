/**
 * Firmware entry — validates everything, listens before sending, then enables RF.
 * Arduino framework contract: setup() once, loop() repeatedly.
 */
#include <Arduino.h>
#include "multiboot.h"
#include "scheduler.h"
#include "radio_arbiter.h"
#include "SX1262Router.hpp"
#include "WebTerminal.hpp"

static bool s_tx_enabled = false;

void setup() {
    multiboot_init();
    SX1262Router_init();
    WebTerminal_init();

    // Concurrent dual-run setup
    multiboot_set_dual_run(true);
    multiboot_load_concurrent(SLOT_MESHTASTIC);
    multiboot_load_concurrent(SLOT_MESHCORE);

    // Gate: nothing transmits until validation passes AND airwaves are free
    const bool gate = SX1262Router_gate();
    s_tx_enabled = gate && SX1262Router_can_tx();
    if (!s_tx_enabled) {
        return;  // stay silent rather than emit RF into an unvalidated state
    }
    multiboot_load_slot(SLOT_RADIO);
    printf("lora-multiboot: validated=1 can_tx=1 concurrent=%u dual=%d\n",
           (unsigned)multiboot_active_concurrent_count(),
           (int)multiboot_dual_run_enabled());
}

void loop() {
    scheduler_tick();
    WebTerminal_tick();
}
