# Changelog

## v1.0.2 - 2026-08-22

### Added
- **Desktop widget mode**: pin the monitor onto the desktop layer itself -
  behind every window, yet persistent across Show Desktop (Win+D), Win+M and
  virtual-desktop switches (Windows WorkerW embedding, Linux desktop-type
  windows, macOS best-effort). Right-click the title to toggle; persisted in
  config.json.
- Rounded glass tile design with soft accent glow, theme-aware palette.
- Manufacturer sensor backends: LibreHardwareMonitor / OpenHardwareMonitor
  WMI namespaces for true CPU/GPU temperatures, loads and fan RPMs.
- GPU usage & temperature tiles via auto-detected nvidia-smi.
- Fan RPM tiles (hardware monitor or psutil on Linux).
- Disk read/write throughput tiles.
- Battery percentage tile (laptops).
- Inferred CPU temperature from sustained load when no hardware source is
  available, honestly labelled `~Temperature`.

### Fixed
- Disk metrics now target the real system drive instead of `/` on Windows.
- Windows temperature detection no longer silently missing.

## v1.0.1 - 2026-08-22

### Added
- SECURITY.md with private vulnerability reporting.
- MIT license, `.gitignore`, `requirements.txt`.

## v1.0.0 - 2026-07-23

Initial release: cross-platform CPU/RAM/disk/network/ping monitoring with
theme selector, dynamic reordering and standalone builds for Windows, Linux
and macOS.
