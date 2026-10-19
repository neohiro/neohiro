# Priority — TX time-division slowdown control

Without priority: every concurrent slot competes equally; high-traffic repeater can be blocked by low-traffic sniffer → slowdown.

Solution: priority field (`uint8_t`) in `scheduler.h` and `radio_arbiter.h`.

| Priority | Value | Slot type | Effect |
|---|---|---|---|
| Critical | 255 | MeshCore Repeater (`MC repeater`), Meshtastic Repeater (`MT repeater`) | Preempts any lower-priority TX; minimal slowdown |
| Normal | 128 | MeshCore Room Server (`MC roomserver`) | Standard arbitration |
| Low | 0 | LoRa Sniffer (pid=0x00 pass-through) | Only transmits when no higher slot needs air; no blocking |

Implementation:
- `scheduler_start_slot()` takes slot_id; priority applied at `arbiter_request()`
- `arbiter_request()` preempts if `prio > s_granted_prio`
- RX remains continuous (promiscuous) regardless of priority; only TX is prioritized
- Zero packet loss preserved: RX never interrupted; only transmission order changes
