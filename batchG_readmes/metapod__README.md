# metapod
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgray.svg)](https://github.com/)
[![Build Status](https://github.com/neohiro/metapod/actions/workflows/release.yml/badge.svg)](https://github.com/neohiro/metapod/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Windows 10 &amp; 11 Hardener — apply curated security &amp; privacy tweaks from a simple GUI.

> ⚠️ **Warning:** this is a strong tool and some settings cannot be undone. It is possible some programs will not work anymore. A registry backup is created automatically before changes are applied.

<img width="1000" height="750" alt="image" src="https://github.com/user-attachments/assets/7192cfdf-c08e-4dca-a88b-d4abda9da32e" />

## ✨ What it does

metapod ships a curated set of hardening tweaks, organised into categories:

| Category | Examples |
| --- | --- |
| **File Associations** | Open `.hta`, `.vbs`, `.js`, `.bat` and other risky formats in Notepad instead of executing them |
| **Windows Defender** | Enable sandboxing and strengthen Defender behaviour |
| **Attack Surface Reduction** | Configure Defender ASR rules |
| **System-Wide Protections** | Extra system-level mitigations |
| **Browser & Office** | Harden the most-abused attack vectors |
| **Privacy & Logging** | Reduce telemetry and data collection |
| **Firewall & Network** | Tighten network exposure |
| **Advanced / Additional Hardening** | Miscellaneous high-impact tweaks |
| **Authentication & Accounts** | Account policy adjustments |
| **Storage & Disk** | Disk-related protections |
| **Updates & Patch Management** | Keep the system patched |
| **Logging & Monitoring** | Improve visibility of what happens on the machine |

Every tweak shows a description in the GUI and can be toggled **on** or **off** individually.

## 🚀 Usage

1. Download the standalone executable from the **[Releases](../../releases)** tab (no Python required), or run from source with `python metapod.PY`.
2. The tool self-elevates: confirm the UAC prompt to run as Administrator.
3. Select the tweaks you want and apply them.
4. Reboot when prompted for all settings to take effect.

A timestamped `RegistryBackup_<date>` folder is written next to the executable so registry values touched by the tool can be restored.

## 📄 License

Released under the [MIT License](LICENSE).

---

<p align="center">
  <a href="https://github.com/sponsors/neohiro"><img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?logo=githubsponsors&style=for-the-badge" alt="GitHub Sponsors"></a>&nbsp;&nbsp;
  <a href="https://www.patreon.com/frenzypenguin_media"><img src="https://img.shields.io/badge/Patreon-frenzypenguin__media-F96854?logo=patreon&style=for-the-badge" alt="Support on Patreon"></a>
</p>
