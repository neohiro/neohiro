# SystemMonitor
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgray.svg)](https://github.com/)
[![Build Status](https://github.com/neohiro/SystemMonitor/actions/workflows/release.yml/badge.svg)](https://github.com/neohiro/SystemMonitor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Multiplatform System Health Monitor for PC.

Autodetects sensors:

- Network usage (+ latency)
- CPU usage & frequency
- RAM usage
- Disk usage, free space **and live read/write throughput**
- CPU temperature - full priority chain: LibreHardwareMonitor/OpenHardwareMonitor → Linux psutil/sysfs → Windows WMI thermal zone → load-based estimate (labelled `~Temp` when inferred)
- GPU usage & temperature (NVIDIA via nvidia-smi, or hardware-monitor backends)
- Fan speeds (hardware monitor / Linux psutil)
- Battery percentage (laptops)

Tiles for optional sensors appear automatically only when the underlying hardware/dependency is available. Install the optional backend once to unlock everything: `pip install wmi` (Windows) and/or run [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) for true motherboard sensor values.

## 🧊 Futuristic tiles

Every device group renders as a rounded glass card with a soft accent glow, theme-aware palette and inline sparkline graphs.

## 📌 Widget mode (lives on your desktop)

Right-click the **System Monitor** title and enable **"Widget mode"** to pin the monitor onto the desktop layer itself:

- **Windows** – embedded into the shell's wallpaper layer (same approach as Rainmeter): it sits *behind every window* — never on top of your programs — yet survives *Show Desktop* (Win+D), Win+M and virtual-desktop switches. Explorer restarts are detected and re-embedded automatically.
- **Linux/X11** – desktop-type window: sticky across workspaces, below other windows, no taskbar entry (wmctrl hints where supported).
- **macOS** – normal window kept out of the way (desktop layer needs PyObjC; best-effort).

The setting is remembered in `~/.config/system-monitor/config.json` and restored on the next launch.

You can switch the order of sensor groups. Boasts a theme selector. Save Log will save the active readings into your Documents. The dynamic tiles are now also able to be reorganised upon window resizing.
A config.json file is included to save the window sizing, the selected theme and favorite order.

<img width="300" height="783" alt="image" src="https://github.com/user-attachments/assets/ed297dcf-dd5b-4d7e-9ba5-084be61ad0ff" />

<details>
<summary>Concept mockup of the dashboard layout</summary>

  <img width="556" height="754" alt="image" src="https://github.com/user-attachments/assets/01f561b8-bfb9-43b5-91b3-7e61198855c9" />

</details>

## 📦 Installation

You can download the compiled standalone release for your operating system (Windows, macOS, or Linux) directly from the **[Releases](../../releases)** tab. No Python installation is required! Just download the .zip for your OS, extract, and run.

## 🛠️ Run from source

```bash
pip install -r requirements.txt
python SystemMonitor.PY
```

## 📄 License

Released under the [MIT License](LICENSE).


---

<p align="center">
  <a href="https://github.com/sponsors/neohiro"><img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?logo=githubsponsors&style=for-the-badge" alt="GitHub Sponsors"></a>&nbsp;&nbsp;
  <a href="https://www.patreon.com/frenzypenguin_media"><img src="https://img.shields.io/badge/Patreon-frenzypenguin__media-F96854?logo=patreon&style=for-the-badge" alt="Support on Patreon"></a>
</p>
