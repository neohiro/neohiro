# Tristar Mania
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgray.svg)](https://github.com/)
[![Build Status](https://github.com/neohiro/TristarMania/actions/workflows/release.yml/badge.svg)](https://github.com/neohiro/TristarMania/actions)

An addictive python game (Linux/Windows/macOS)

- GREEN TRIANGLE = NEUTRAL SHIP
- RED SQUARE = ENEMY VESSEL
- PINK ARROW = YOUR SHIP
- GREY ASTEROIDS = RESOURCES
- BLACK HOLE = AVOID IT'S ATTRACTION
- NEBULA = DISTORTION IMMINENT

<img width="1920" height="1080" alt="screenshot_20251209_182314" src="https://github.com/user-attachments/assets/8e5be373-934f-4a89-acd2-9761ed8ae91d" />

Tips & Tricks:

- You can cross the screen edges, other objects cannot
- Shoot asteroids for immediate repairs
- Save the 4-letter code to keep your level next time


Version 1.2 changelog:

# Tristar Mania: Major Update Changelog

---

## 🎨 Visual Overhaul & Graphics

 The rendering pipeline has been significantly upgraded to support more complex geometry and particle effects.

### 1. Parallax Background
* **New:** Implemented a `ParallaxStar` class. These stars are fainter and move based on the player's delta movement (`player_dx`, `player_dy`), creating a depth/3D effect relative to the foreground.
* **Old:** Static falling starfield only.

### 2. Procedural Asteroids
* **New:** `SpaceRock` now generates random polygons (7-12 points) with varying radii to create jagged, rock-like shapes. They also feature rotation mechanics and a distinct outline.
* **Old:** Simple grey circles drawn using `pygame.draw.circle`.

### 3. Laser Effects
* **New:** Lasers are now rendered as rotated surfaces to match their travel direction. They include a "glow" effect (a larger, translucent circle centered on the laser head).
* **Old:** Simple, non-rotated rectangles.

### 4. Boss Design (3D Effect)
* **New:** The Boss is no longer a flat square. It is drawn using multiple polygons to create a "beveled" 3D pyramid look with shading (light top, dark bottom). It features a pulsating red "core" eye in the center.
* **Old:** A solid, flat red square (`ENEMY_COLOR`).

### 5. Engine Trails
* **New:** Added `TrailParticle` class. The player's ship now emits cyan particles from the rear when moving forward, which fade out over time.
* **Old:** No engine trails implemented.

---

## 🎮 Gameplay & AI Changes

### Boss AI & Difficulty
* **Movement Logic:** The Boss now utilizes a timer to switch behaviors between **tracking the player** (60% chance) and **moving to a random point** in the upper screen (40% chance). Previously, it only tracked the player directly.
* **Dual Bosses:** At **Level 8+**, two bosses will now spawn simultaneously. To balance this, the HP multiplier for bosses was reduced from `2.0` to `1.2` when in dual mode.

### Screen Shake
* **Implementation:** The game now renders to a temporary `display_surface` instead of directly to the screen. This allows the entire game world to be offset by random X/Y values (`shake_offset`) during high-impact events (taking damage, destroying a boss).

### Neutral Ships
* **Spawning:** Neutral ships now spawn exclusively at the screen edges (Top, Bottom, Left, Right) and fly across the screen.
* **Old Behavior:** Spawned at random coordinates and wrapped around screen edges.

### Invulnerability Feedback
* **New:** The Lifebar UI now flashes white and red when the player is down to **1 Life**.

---

## ⚙️ System & Quality of Life

### Resolution & Display
* **4K Support:** Added `(3840, 2160)` to the resolution list.
* **Scaling:** Implemented `pygame.SCALED` flag. This ensures the window contents scale up properly on high-DPI monitors or when fullscreen is active on lower resolutions.

### Screenshots
* **New Feature:** Pressing `F12` or `PRINTSCREEN` saves a timestamped PNG of the current frame to the user's `Pictures/TristarMania` folder.
    * *Dependencies:* Added `import os` and `from datetime import datetime`.

---

## ⚖️ Balance & Progression

### Leveling Formula
The difficulty curve has been steepened significantly.

* **Old Formula:**
    ```python
    score_needed = Level * (475 + 25 * Level)
    ```
* **New Formula:**
    ```python
    score_needed = Level * (600 + 100 * Level)
    ```

### Level Up Timer
* The text popup for "LEVEL UP" is now faster, lasting **60 frames** (1 second) instead of the previous implicit duration.

---

## 📝 Summary Comparison Table

| Feature | Legacy Version | New Version |
| :--- | :--- | :--- |
| **Asteroids** | Circles | Rotating Polygons |
| **Boss Visuals** | Flat Red Square | 3D Beveled Pyramid |
| **Boss Count** | Single | Double (Level 8+) |
| **Lasers** | Rectangles | Rotated Sprites + Glow |
| **Player Ship** | Standard | Added Engine Trails |
| **Impact Feel** | Standard Audio | **Screen Shake** + Sparks |
| **Max Res** | 1080p | 4K (2160p) |
| **Screenshots** | None | F12 / PrintScreen |
| **Render Method** | Direct to Screen | Intermediate Surface (for shake) |

## 📦 Installation

You can download the compiled standalone release for your operating system (Windows, macOS, or Linux) directly from the **[Releases](../../releases)** tab. No Python installation is required! Just download the .zip for your OS, extract, and run.


---

<p align="center">
  <a href="https://github.com/sponsors/neohiro"><img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?logo=githubsponsors&style=for-the-badge" alt="GitHub Sponsors"></a>&nbsp;&nbsp;
  <a href="https://www.patreon.com/frenzypenguin_media"><img src="https://img.shields.io/badge/Patreon-frenzypenguin__media-F96854?logo=patreon&style=for-the-badge" alt="Support on Patreon"></a>
</p>
