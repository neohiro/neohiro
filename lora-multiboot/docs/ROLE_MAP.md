# Role Map — lora-multiboot

User spec (auto-implemented with safe defaults):
- 2x Repeater (slots 0, 1)
- 1x Meshtastic (slot 2)
- 1x MeshCore (slot 3)
- 1x Radio / base (slot 4)

Total: 5 slots on single SX1262 / ESP32, 1 MiB each, non-destructive updates.

Simultaneous execution (`dual_run`) activates Meshtastic + MeshCore together
while repeaters remain in background provisioning slots.
