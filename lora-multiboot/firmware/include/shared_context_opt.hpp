/*
 * Shared context — minimal RAM, extensible PIDs for EU-frequency meshes
 * Reduction: dynamic PID table replaces hardcoded ternary; 128-byte default option.
 */
#ifndef SHARED_CONTEXT_OPT_HPP
#define SHARED_CONTEXT_OPT_HPP
#include <stdint.h>

// Configurable: 128 for low-RAM nodes, 256 for high-throughput
#ifndef SHARED_RX_BUF_LEN
#define SHARED_RX_BUF_LEN 128
#endif

// Extensible PID table — other EU-frequency meshes add entries here
// Less code than hardcoded ternary; one loop classifies any registered PID.
// PID table — same PID can serve multiple roles (meshcore repeater, room, etc.)
// All RX (pid=0x00) also copies to sniffer concurrently.
#define MAX_PIDS 8
static const uint8_t s_pid_table[MAX_PIDS] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };

typedef struct {
    uint8_t  buf[SHARED_RX_BUF_LEN];
    uint16_t len;
    uint8_t  pid;
    uint32_t rssi;
    bool     relayed;
} shared_context_t;

inline bool shared_context_classify(shared_context_t* c) {
    if (c->len == 0) return false;
    uint8_t b = c->buf[0];
    for (uint8_t i = 0; i < MAX_PIDS; ++i) {
        if (b == s_pid_table[i]) { c->pid = b; return true; }
    }
    /* LoRa sniffer / unknown PID: pass-through (no filter) */
    c->pid = 0x00;
    return true;  // treat as relay-all: RX copied to running firmware
}

#endif
