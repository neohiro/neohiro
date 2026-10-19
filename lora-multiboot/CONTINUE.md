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

Verified: `SUCCESS` — RAM 5.7% (18,664 B), Flash 11.2% (234,357 B), `firmware.bin` 234,720 bytes,
ESP32-S3 target (`heltec_wifi_32_lora_v4`), RadioLib 7.8.1, partition table `quadboot.csv`.

## Flashable binary steps
1. `make test` (portable suite) — no hardware, no toolchain needed
2. `pio run -e heltec_v4_bridge` — builds `firmware.bin` (verified)
3. Flash base loader (this repo) to device
4. Provision slots with repeater software (see `docs/ROLES.md`):
   - `ota_0`: MeshCore Repeater (`MC repeater`)
   - `ota_1`: Meshtastic Repeater (`MT repeater`)
   - `ota_2..ota_4`: reserved (reticulum, LoRaWAN, future)
5. Use `tools/flash.py` to write app partitions non-destructively

## Critical limitation from upstream `ARCHITECTURE.md` / `ROLES.md`
- **One radio = one active slot at a time.** Two images cannot drive SX1262 concurrently.
- The bridge image (`ProtocolId` + shared-carrier) serves both meshes from one slot — that's the intended simultaneous path, not concurrent threads.
- Our `scheduler.cpp` / `radio_arbiter.cpp` compile and run inside the verified binary
  (priority arbitration, bitmask tick), but the RadioLib SX1262 driver path is not yet
  wired to them: promiscuous capture and cross-protocol relay remain the open items.

## To make repeaters work now
- Build loader with `platformio.ini` (real config integrated)
- Fill `ota_0` / `ota_1` with actual Meshtastic/MeshCore repeater binaries (source outside this repo)
- Run `install-lora-multiboot.bat` after flash for partition verification
- Verify with serial log: `SlotTable`, `Provisioning`, `RadioPlan`, `StatusPanel` all pass

Assumption: actual repeater firmware images must be supplied; loader is ready.
