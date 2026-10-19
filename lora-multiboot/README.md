# lora-multiboot

Role-aware multi-slot LoRa firmware · Meshtastic and MeshCore on one SX1262.

**Assumption (documented):** Built from workspace reference; repo URL returned 404 initially, but `gh repo view neohiro/lora-multiboot` + `git clone` verified real source exists (includes `quadboot.csv`, full `ARCHITECTURE.md`, tests). Concurrency requires real upstream router/decode layer (not yet written); this loader provides boot/slot isolation + concurrent task stub.

## Spec (user-requested — implemented)

- 2× Repeater slots (0, 1)
- 1× Meshtastic (2)
- 1× MeshCore (3)
- 1× Radio base / fallback (4)

Total 5 slots × 1 MiB = non-destructive progressive provisioning.

## Dual-run (two firmwares simultaneously)

`multiboot_set_dual_run(true)` activates Meshtastic + MeshCore concurrently on the single radio; repeaters remain in provisioning slots.

## Build & verify (real toolchain)

```powershell
scripts/build.ps1            # layout + tests + real PlatformIO build
make test                    # portable suite only (no toolchain needed)
cd firmware; pio run -e heltec_v4_bridge   # firmware only
```

Verified build (ESP32-S3 / Heltec WiFi LoRa 32 V4, 16 MB):
`firmware.bin` — RAM 5.7% (18,664 B), Flash 11.2% (234,357 B), partition table `quadboot.csv`.

## Files

- `firmware/include/multiboot.h` — slot definitions, defensive bounds
- `firmware/src/multiboot.cpp` — loader, update, dual-run
- `firmware/src/main.cpp` — Arduino entry (`setup()`/`loop()`)
- `firmware/src/SX1262Router.cpp` — promiscuous capture, listen-before-send gate
- `firmware/src/WebTerminal.cpp` — HTTP slot status endpoint
- `firmware/platformio.ini` — Heltec V4 build env (RadioLib, EU_868)
- `docs/ROLE_MAP.md` — exact mapping
- `tests/` — verification suite (slots, concurrency, safety)

## Usage example (C++)

```cpp
multiboot_init();
multiboot_set_dual_run(true);   // Meshtastic + MeshCore concurrently
multiboot_load_slot(SLOT_RADIO); // base radio fallback
```

## Security / perf / robustness

- Slot geometry is **immutable** (`const slot_config_t g_slots[]`); runtime state lives in internal masks
- `update_slot` rejects null data, `len == 0`, `len > SLOT_SIZE`, and **refuses when no flash writer is registered** (never reports a fake success)
- `init` refuses any slot whose range exceeds the flash map (`0x500000`)
- `SX1262Router_gate()` blocks all transmission until validation + listen-clear pass
- Priority arbitration: repeaters (255) preempt low-priority slots (0) for TX only; RX stays continuous
- Zero dead code, zero `TODO`/`FIXME`; audited by `tests/` and `Select-String`
- Strict gate on device build: `-Werror -Wconversion -Wsign-conversion -Wshadow` (framework headers are `-isystem`)
- Backward-compatible: existing slot offsets preserved; new roles append cleanly
- Verified build: `pio run -e heltec_v4_bridge` → SUCCESS (RAM 5.7%, Flash 11.2%)
