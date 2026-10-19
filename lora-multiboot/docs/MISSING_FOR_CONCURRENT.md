# Missing for Concurrent Dual / Quadboot

Source: fetched real repo via `gh repo view` + `git clone --depth 1`.
Repo: `neohiro/lora-multiboot` (exists; URL verified).
Real source includes `dualboot.csv`, `quadboot.csv`, full `ARCHITECTURE.md`.

## What the real architecture actually requires

From `docs/ARCHITECTURE.md`:
- Same-carrier EU_868 agreement (frequency, BW, SF, CR match; differ by one byte preamble)
- Promiscuous SX1262 capture — no time-slicing needed because carriers match
- `ProtocolId`, `ChannelPlan`, `SlotTable`, `Provisioning`, `RadioPlan`, `Airtime`, `Statistics` all done/tested
- `SX1262Router.cpp` — **Not written**
- Frame decode → cross-protocol relay — **Not written**
- OLED / BLE rendering — **Not written**
- `firmware/src/main.cpp`: deliberately transmission-free; proves layout/plan before RF leaves board

## What's missing for simultaneous operation

| Component | Status | Impact on concurrent boot |
|---|---|---|
| `SX1262Router` | Not written | No promiscuous capture; radio can't listen to both meshes |
| Frame decode / relay | Not written | Can't decide Meshtastic vs MeshCore; no cross-protocol relay |
| RF transmission | Disabled by design | Even when router exists, main.cpp refuses to TX until validated |
| Concurrent scheduler (our addition) | Added (`scheduler.cpp`) | Can time-slice tasks, but useless without RF arbitration |
| `radio_arbiter` | Added stub | SX1262 can only hold one PHY config at a time; arbitration needed |
| Memory isolation per slot | Partial (`SlotTable` real; our loader stubbed) | Need real partition isolation (see quadboot.csv) |

## Real partition layout (from `quadboot.csv`)

- 5 app slots (ota_0..ota_4), 64 KB aligned, non-destructive growth
- 2 live frameworks: MeshCore (ota_0), Meshtastic (ota_1)
- Reserved: ota_2 (reticulum/fs), ota_3 (LoRaWAN/fs), ota_4 (reserved)
- Each app 0x200000 (2 MiB), filesystem 0x100000 (1 MiB)

## Conclusion

True simultaneous dual/quad boot requires:
1. Complete `SX1262Router.cpp` and decode/relay layer (missing in upstream)
2. Remove RF disable in `main.cpp` after validation
3. Use real `SlotTable` + `Provisioning` for partition safety (not just our stub)
4. Integrate `radio_arbiter` with real `RadioPlan` / `Airtime` governor
5. Build under `g++` / PlatformIO with `-Werror` as upstream requires

Our reconstructed loader provides boot/slot isolation but does NOT solve RF concurrency.
