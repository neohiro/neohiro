# How to continue — Heltec V4 flashable binary (repeater + Meshtastic + MeshCore)

Source verified via `gh`; real repo files integrated.

## What you need
- Heltec WiFi LoRa 32 V4 (16 MB flash; `heltec_wifi_32_lora_v4.json` defines board)
- PlatformIO + ESP32 core (`platformio.ini` from real repo)
- Actual firmware blobs for Meshtastic (ota_1 / fs_meshtastic) and MeshCore (ota_0 / fs_meshcore) — not vendored in upstream
- `BRIDGE_REGION=EU_868` (shared carrier; only region where both defaults agree)

## Build command (from workspace)
```powershell
# Real build environment copied to firmware/
cd firmware
pio run -e heltec_v4_bridge -t build
# Flash via USB (PlatformIO uploads to 16MB partition table)
pio run -e heltec_v4_bridge -t upload
```

## Flashable binary steps
1. `make check` (host gate) — needs `g++`; validates SlotTable, ChannelPlan, Airtime, Roles without hardware
2. Build `heltec_v4_bridge` with `quadboot.csv` partition (5 slots, 64 KB aligned)
3. Flash base loader (this repo) to device
4. Provision slots with repeater software (see `docs/ROLES.md`):
   - `ota_0`: MeshCore Repeater (`MC repeater`)
   - `ota_1`: Meshtastic Repeater (`MT repeater`)
   - `ota_2..ota_4`: reserved (reticulum, LoRaWAN, future)
5. Use `tools/flash.py` to write app partitions non-destructively

## Critical limitation from upstream `ARCHITECTURE.md` / `ROLES.md`
- **One radio = one active slot at a time.** Two images cannot drive SX1262 concurrently.
- The bridge image (`ProtocolId` + shared-carrier) serves both meshes from one slot — that's the intended simultaneous path, not concurrent threads.
- Our `scheduler.cpp`/`arbiter.cpp` are stubs for future concurrent work; upstream does not support concurrent RF transmission.

## To make repeaters work now
- Build loader with `platformio.ini` (real config integrated)
- Fill `ota_0` / `ota_1` with actual Meshtastic/MeshCore repeater binaries (source outside this repo)
- Run `install-lora-multiboot.bat` after flash for partition verification
- Verify with serial log: `SlotTable`, `Provisioning`, `RadioPlan`, `StatusPanel` all pass

Assumption: actual repeater firmware images must be supplied; loader is ready.
