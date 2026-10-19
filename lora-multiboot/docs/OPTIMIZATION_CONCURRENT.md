# Optimization — two firmwares concurrent, smooth, zero loss, low resource

Real constraint (from `ARCHITECTURE.md` / `ROLES.md`): **one SX1262 = one active slot**. 
True RF concurrency is impossible; the solution is **shared-carrier promiscuous capture + bridge stack**.

## How to make it work without packet loss

1. **Shared-carrier agreement (EU_868)** — both meshes agree on freq, BW, SF, CR. Real repo confirms this only region where defaults align.
2. **Promiscuous RX** (`SX1262Router_init`) — listen to both preambles continuously; don't switch PHY.
3. **Fast ProtocolId** (`PROTOCOL-ID.md`) — classify in first byte after sync word; eliminates decode lag.
4. **Shared context / zero-copy buffer** (`shared_context_opt.hpp`) — single `uint8_t[256]` RX buffer, not two stacks. Low RAM/CPU.
5. **Time-division TX only** (`radio_arbiter.h`) — arbitration needed only for transmission, not reception. RX is continuous.
6. **Bridge image (one slot)** — `Roles.md`: the bridge is one framework containing both stacks; this is the intended concurrent path, not two separate active slots.

## Performance impact
- RX: continuous, no switching → zero packet loss on either mesh
- TX: arbitration gives slices; low overhead because PHY config doesn't change (same carrier)
- RAM: 256 bytes shared vs 2× full stack buffers
- CPU: 1-byte tag instead of full protocol decode on every frame

## Implementation path
- Use `shared_context_opt.hpp` with `SX1262Router.cpp` (promiscuous)
- Build bridge image into `ota_0` or `ota_1`; load via `multiboot_load_slot()`
- Keep `scheduler_tick()` for non-RF tasks only; RF is continuous
- Do NOT attempt concurrent threads on SX1262 — hardware prevents it
