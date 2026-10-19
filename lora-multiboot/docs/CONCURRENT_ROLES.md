# Concurrent Roles — 4 slots at once on Heltec V4 (EU_868)

Same radio (SX1262) serves all via promiscuous capture + bridge image. Time-division only for TX.

| Concurrent Slot | Role | PID | Behavior |
|---|---|---|---|
| 0 | MeshCore Repeater | 0x01 (PID_MESHCORE) | RX filtered to meshcore; relayed |
| 1 | Meshtastic Repeater | 0x02 | RX filtered to meshtastic; relayed |
| 2 | MeshCore Room Server | 0x01 (same PID) | Shares meshcore PID; same RX stream |
| 3 | LoRa Sniffer / Unknown | 0x00 | Receives ALL RX (unknown PIDs also) — no filter |

Rules:
- `PID_MESHCORE` (0x01) can be assigned to multiple valid firmwares simultaneously (repeater + room server share PID).
- Unknown PID (0x00) copies full RX to sniffer concurrently with no packet loss.
- `shared_context_opt.hpp`: single 128-byte buffer; `scheduler_tick()` manages concurrent tasks; `radio_arbiter` handles TX arbitration.
- Build: `pio run -e heltec_v4_bridge -t build` with `BRIDGE_REGION=EU_868`.
