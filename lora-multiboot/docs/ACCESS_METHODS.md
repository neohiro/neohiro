# Access & Firmware Selection — Heltec V4 (WiFi / BLE / USB / Slot)

## Choosing firmware (not USB adapter per slot)
- One board, one USB-serial adapter (`install-lora-multiboot.bat`). Flash loader once; loader selects slot via `SlotLifecycle` / bootloader.
- On-device selection: `StatusPanel` (3-line OLED/CLI) + button / CLI menu in `firmware/src/main.cpp`. No second adapter needed.
- Remote selection via BLE/WiFi only when slot is live (see below).

## BLE detects active firmware
- Active slot advertises its `SlotTable` entry (name + role) via ESP32 BLE.
- `StatusPanel` renders: `MC repeater`, `MT router`, `MeshCore Room`, etc. — from `SlotLifecycle` state.
- Unknown / sniffer (`pid=0x00`) can also advertise `SNIF` status for tool discovery.

## WiFi points per active slot
- Only the **running slot** owns WiFi/BLE interfaces (one radio = one active framework at a time; `ROLES.md`).
- Meshtastic active → Meshtastic WiFi/BLE endpoints.
- MeshCore active → MeshCore endpoints.
- Bridge image (`PROTOCOL-ID.md` / `ARCHITECTURE.md`) serves both meshes from **one** slot with shared WiFi/BLE.
- WiFi does not switch independently per slot while slot is running; use `SlotLifecycle` to change active framework.

## USB role (single adapter, all slots)
- `tools/flash.py` writes to partition (`ota_0`, `ota_1`, etc.) non-destructively.
- `install-lora-multiboot.sh/bat` validates layout after flash.
- USB is programming/verification path, not runtime access for every slot.

## Concurrent access (dual/quad)
- USB: programming only; concurrent slots use `scheduler_tick()` + `shared_context_opt.hpp`
- BLE: active slot only broadcasts; other slots are loaded but not broadcasting until promoted by `SlotLifecycle`
- WiFi: same — active slot uses it; concurrent tasks (scheduler) do not independently open WiFi sockets
