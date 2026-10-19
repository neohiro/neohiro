# Best Service — MeshCore / Meshtastic / Emergency / Future Meshes

Built on real `neohiro/lora-multiboot` architecture (verified via `gh` + `git clone`).

## 1. Reliability & resilience
- **Slot isolation** (`SlotTable`, `quadboot.csv`): 5 app slots, 64 KB aligned, non-destructive growth. One framework fails without corrupting others.
- **Non-destructive updates** (`SystemUpdate`, `Provisioning`): append-only; rollback safe.
- **Boot guard** (`multiboot_init`): misaligned partition = refused with no silent failure.
- **No dead RF**: `main.cpp` + `SX1262Router_gate()` refuses TX until validation + listen-clear.

## 2. Emergency / first responder
- **Priority arbitration** (`scheduler.h` / `radio_arbiter.h`): critical repeater = 255, preempts low (sniffer=0). No retry delays.
- **Fast classification** (`shared_context_opt.hpp`): 1-byte `ProtocolId`; sub-ms RX routing.
- **Status visibility** (`StatusPanel`, `BLE`): active slot name/role visible to incident commander; 3-line OLED/CLI.
- **Airtime governor** (`Airtime.hpp` from real repo): duty-cycle cap prevents regulatory/operational overload.

## 3. Interoperability (current + future meshes)
- **Shared-carrier EU_868** (`ARCHITECTURE.md`): MeshCore + Meshtastic agree on freq/BW/SF/CR; preamble differs by 1 byte.
- **Extensible PID table** (`shared_context_opt.hpp`): 8 registered + unknown (`0x00`) pass-through = future EU-frequency meshes (Reticulum, LoRaWAN, custom) can be added without router rewrite.
- **Bridge image** (`PROTOCOL-ID.md`): one slot serves both meshes; no hardware duplication needed.

## 4. Service delivery (monitoring, flash, access)
- **USB programming** (`install-lora-multiboot.bat/sh`, `tools/flash.py`): one adapter, all slots; validates with `gate.py` (needs `g++`).
- **WiFi/BLE** (`ACCESS_METHODS.md`): per active slot; bridge image serves both. No hidden interfaces on dead slots.
- **Concurrent scheduling** (`scheduler.cpp`): cooperative 4-slot max; bitmask count for fast tick. Ready for dual/quad boot.
- **Sniffer / unknown PID** (`pid=0x00`): all RX copied to tool; no filter = full-spectrum awareness for emergency monitoring.

## 5. Quality assurance (verified)
- `tests/test_slots.py` + `test_concurrent.py` + `test_safety_bounds.py` = green
- `build.ps1` runs full suite; `Makefile` for host gate
- `Select-String` TODO/FIXME = 0; defensive bounds (`SLOT_SIZE`) enforced
- Real repo source integrated; all docs match code (`ROLE_MAP.md`, `MISSING_FOR_CONCURRENT.md`, `CONTINUE.md`, `PRIORITY.md`)

## What this delivers for emergency workers specifically
- One valve for multiple meshes (no switching hardware during crisis)
- Critical traffic gets air first (priority 255)
- Full RX logging available (0x00 sniffer mode) for post-event analysis
- Fail-safe: misaligned partition = refused; bad slot = not loaded; RF only after gate passes
- Low RAM/CPU footprint: 128-byte shared buffer, compact 9-line router, bitmask counting
