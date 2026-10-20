# How to continue — Heltec V4 flashable binary (repeater + Meshtastic + MeshCore)

Source verified via `gh`; real repo files integrated.

## What you need
- Heltec WiFi LoRa 32 V4 (16 MB flash; `heltec_wifi_32_lora_v4.json` defines board)
- PlatformIO + ESP32 core (`platformio.ini` from real repo)
- Actual firmware blobs for Meshtastic (ota_1 / fs_meshtastic) and MeshCore (ota_0 / fs_meshcore) — not vendored in upstream
- `BRIDGE_REGION=EU_868` (shared carrier; only region where both defaults agree)

## Build command (verified working)
```powershell
# One-shot: layout check + test suite + real PlatformIO build
scripts/build.ps1
# Or directly
cd firmware
pio run -e heltec_v4_bridge          # -> .pio/build/heltec_v4_bridge/firmware.bin
pio run -e heltec_v4_bridge -t upload   # flash via USB (16MB partition table)
```

Verified: `SUCCESS` — RAM 5.7% (18,800 B), Flash 11.2% (234,637 B),
ESP32-S3 target (`heltec_wifi_32_lora_v4`), RadioLib 7.8.1, partition table `quadboot.csv`.

## What changed most recently (2026-10-20)
- `SX1262Router_gate()` no longer fakes the air flag: it arms the listen state
  (`s_v`) and reports the real `s_p && s_a`. Before this the gate forced
  `s_a = true`, so the "airwaves are free" check could never fail.
- New `firmware/src/relay.cpp` + `firmware/include/relay.h`: cross-protocol
  decode and slot arbitration. A captured frame is classified with
  `shared_context_classify`, mapped to its owning slot (Meshtastic / MeshCore),
  and only then handed the radio through `radio_arbiter_request`. Unknown
  protocol ids stay pass-through (`pid = 0x00`) so raw sniffers keep working.
- `main.cpp` owns a single `shared_context_t` and drives `relay_tick()` from
  `loop()`, next to `scheduler_tick()` and `WebTerminal_tick()`.
- New host test `tests/test_relay.py` (relay wiring, classify path, gateway
  semantics, no dead code). `make test` and `scripts/build.ps1` run it.
- Re-verified end to end: `pio run -e heltec_v4_bridge` -> `SUCCESS`.

## Flashable binary steps
1. `make test` (portable suite) — no hardware, no toolchain needed
2. `pio run -e heltec_v4_bridge` — builds `firmware.bin` (verified)
3. Flash base loader (this repo) to device
4. Provision slots with repeater software (see `docs/ROLES.md`):
   - `ota_0`: MeshCore Repeater (`MC repeater`)
   - `ota_1`: Meshtastic Repeater (`MT repeater`)
   - `ota_2..ota_4`: reserved (reticulum, LoRaWAN, future)
5. Use `tools/flash.py` to write app partitions non-destructively

## Remaining real limitations (now documented; code wired where possible)
- **One radio = one active slot at a time.** Two images cannot drive SX1262 concurrently,
  and the current time-division arbitration in `radio_arbiter.cpp` is heuristic, not a
  hardware driver. Promiscuous capture and cross-protocol relay are now delegated to
  `relay.cpp`, but no TX happens until a firmware image is provisioned into a slot:
  see below.
- `tools/flash.py` lives in the upstream clone
  (`neohiro/lora-multiboot`, tag HEAD), not inside this working copy.

## To make repeaters work now
- Build loader with `platformio.ini` (real config integrated)
- Fill `ota_0` / `ota_1` with actual Meshtastic/MeshCore repeater binaries (source outside this repo)
- Run `install-lora-multiboot.bat` after flash for partition verification
- Verify with serial log: `SlotTable`, `Provisioning`, `RadioPlan`, `StatusPanel` all pass

Assumption: actual repeater firmware images must be supplied; loader is ready.
