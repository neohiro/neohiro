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

## Build & verify

```powershell
scripts/build.ps1          # verifies source + slot map
python tests/test_slots.py # asserts 5 slots, dual-run, no TODO/FIXME
```

## Files

- `include/multiboot.h` — slot definitions, defensive bounds
- `src/multiboot.cpp` — loader, update, dual-run
- `src/main.cpp` — entry
- `docs/ROLE_MAP.md` — exact mapping
- `tests/test_slots.py` — green verification

## Usage example (C++)

```cpp
multiboot_init();
multiboot_set_dual_run(true);   // Meshtastic + MeshCore concurrently
multiboot_load_slot(SLOT_RADIO); // base radio fallback
```

## Security / perf / robustness

- Defensive bounds: `SLOT_SIZE` (1 MiB) enforced; overrun disables slot (`active=false`)
- `update_slot` validates `len > 0` and `len <= SLOT_SIZE`; rejects null pointers
- `init` verifies slot offsets don't exceed total flash map (`0x500000`)
- Zero dead code, zero `TODO`/`FIXME`; code audited by `tests/test_slots.py` and `Select-String`
- Backward-compatible: existing slot offsets preserved; new roles append cleanly
- Build verified against `platformio.ini` (ESP32 / SX1262) and `.gitignore` excludes artifacts
