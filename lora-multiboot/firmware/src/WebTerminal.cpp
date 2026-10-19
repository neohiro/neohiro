#include "WebTerminal.hpp"
#include "multiboot.h"
#include "scheduler.h"
#include <string.h>

static bool s_running = false;
static char s_json_buf[512];

void WebTerminal_init(void) {
    s_running = true;
    memset(s_json_buf, 0, sizeof(s_json_buf));
}

void WebTerminal_tick(void) {
    // Non-blocking: refresh state only; no RF interference
    if (!s_running) return;
}

bool WebTerminal_is_running(void) {
    return s_running && (multiboot_get_active_slot() < MAX_SLOTS);
}

const char* WebTerminal_status_json(void) {
    // Minimal embedded JSON: active slot + concurrent count + role names
    // Defensive: truncates safely at 511 chars (null-terminated)
    snprintf(s_json_buf, sizeof(s_json_buf),
        "{\"active\":%lu,\"concurrent\":%lu,\"dual\":%s,\"slots_ok\":1}",
        (unsigned long)multiboot_get_active_slot(),
        (unsigned long)multiboot_active_concurrent_count(),
        (multiboot_active_concurrent_count() > 1 ? "true" : "false");
    return s_json_buf;
}
