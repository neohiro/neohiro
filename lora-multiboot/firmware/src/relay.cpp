/*
 * Relay — cross-protocol decode and slot arbitration.
 *
 * One radio (SX1262) can only hold a single PHY configuration, so two
 * protocol stacks never transmit at the same time. The relay therefore:
 *   1. classifies a captured frame (shared_context_classify),
 *   2. maps the protocol id to the owning slot,
 *   3. asks the arbiter for the radio before the owner may transmit.
 *
 * Frames with an unknown protocol id are passed through untouched
 * (shared_context_classify sets pid = 0x00), which keeps raw sniffers
 * working and never silently drops traffic.
 */
#include "relay.h"
#include "multiboot.h"
#include "radio_arbiter.h"
#include <string.h>

/* Protocol id -> owning slot. Meshtastic and MeshCore share one carrier
 * in EU_868, so a captured frame can be attributed to either stack. */
static uint32_t slot_for_pid(uint8_t pid) {
    switch (pid) {
        case 0x01: return SLOT_MESHTASTIC;  /* Meshtastic data */
        case 0x02: return SLOT_MESHTASTIC;  /* Meshtastic text */
        case 0x03: return SLOT_MESHCORE;    /* MeshCore advert */
        case 0x04: return SLOT_MESHCORE;    /* MeshCore data */
        default:   return 0xFFFFFFFFu;      /* unknown: no owner */
    }
}

void relay_init(void) {
    arbiter_init();
}

bool relay_tick(shared_context_t* ctx) {
    if (ctx == NULL) return false;
    if (!shared_context_classify(ctx)) return false;

    /* Unknown protocol id: pass-through, no arbitration, no ownership. */
    if (ctx->pid == 0x00) {
        ctx->relayed = false;
        return false;
    }

    const uint32_t owner = slot_for_pid(ctx->pid);
    if (owner == 0xFFFFFFFFu) {
        ctx->relayed = false;
        return false;
    }
    if (!multiboot_slot_usable(owner)) {
        ctx->relayed = false;
        return false;
    }

    /* The radio is granted to the owning slot for a short slice. The
     * arbiter refuses the request when a higher priority slot holds it,
     * in which case the frame stays un-relayed and is retried later. */
    const bool granted = arbiter_request(owner, 10, 1);
    ctx->relayed = granted;
    if (granted) {
        arbiter_release(owner);  /* frame handled — don't leak the grant */
    }
    return granted;
}
