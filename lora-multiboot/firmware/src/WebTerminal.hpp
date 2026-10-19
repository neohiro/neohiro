/*
 * WebTerminal — minimal HTTP management interface for active firmware slots
 * Provided automatically when WiFi interface is available (ESP32 Arduino framework).
 * Defensive: never interferes with RF scheduling; only reports/manages state.
 */
#ifndef WEBTERMINAL_HPP
#define WEBTERMINAL_HPP
#include <stdint.h>
#include <stdbool.h>

void WebTerminal_init(void);
void WebTerminal_tick(void);  // call from loop; non-blocking
bool WebTerminal_is_running(void);
// Returns JSON status of all slots; safe for embedded string build
const char* WebTerminal_status_json(void);
#endif
