# ZombieShoot
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgray.svg)](https://github.com/)
[![Build Status](https://github.com/neohiro/ZombieShoot/actions/workflows/release.yml/badge.svg)](https://github.com/neohiro/ZombieShoot/actions)

Zombie Shooter for Linux, Windows, and macOS

<img width="1371" height="877" alt="image" src="https://github.com/user-attachments/assets/2dcd4b1f-6219-4c80-9cf4-ca76964ec2c3" />

ZombieShoot.PY
- A fast-paced, top-down zombie shooter game built with Pygame. Survive endless waves of the undead, upgrade your weapons, and climb the leaderboards in this retro-inspired arcade action title.

Features

- Dynamic Gameplay: Face off against an ever-increasing horde of zombies with a simple and intuitive top-down perspective.
- Weapon Upgrades: Start with a basic pistol and progress to powerful weapons like the machine gun and the devastating Gatling gun.
- Procedural Generation: The game world features a procedurally generated hexagonal floor pattern, ensuring every session feels unique.
- Session Leaderboards: Your best scores are tracked for every run, so you can compete against yourself to survive longer.
- Customizable Controls: The game's controls can be fully remapped in the options menu to suit your play style.
- In-House Sound Generation: All sound effects and the main menu music are generated programmatically, providing a unique and consistent audio experience.
- Visual Effects: Get into the action with visual feedback from blood splatters and particle effects when you take down a zombie.

How to Play
- Run the Game: Make sure you have Pygame installed (pip install pygame) and then run the Python script.

Controls:

- Movement: Use the W, A, S, D keys or the arrow keys to move your character.
- Shooting: Aim with your mouse and click to shoot.
- Survive: Your goal is to survive for as long as possible while your score increases. As time goes on, the zombie waves will become more difficult.
- Power-Ups: Keep an eye out for health-restoring power-ups to stay in the fight longer.

Technical Details
- Language: Python
- Libraries: pygame, numpy, math, random
- Game Loop: The core of the game is a robust state machine that handles transitions between the main menu, options, leaderboards, and the primary game loop.
- Object-Oriented Design: The game is structured with classes for Player, Zombie, Bullet, PowerUp, and other game entities, making the code clean and easy to manage.

Installation
To get started, simply download this repository and install the required libraries:

    git clone https://github.com/neohiro/ZombieShoot.git
    cd ZombieShoot
    pip install -r requirements.txt
    python ZombieShoot.PY

Contributing
- Feel free to open an issue or submit a pull request if you have ideas for new features or improvements!

## 📦 Installation

You can download the compiled standalone release for your operating system (Windows, macOS, or Linux) directly from the **[Releases](../../releases)** tab. No Python installation is required! Just download the .zip for your OS, extract, and run.

🔗 [frenzypenguin.media](https://linktr.ee/frenzypenguin.media)

---

<p align="center">
  <a href="https://github.com/sponsors/neohiro"><img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?logo=githubsponsors&style=for-the-badge" alt="GitHub Sponsors"></a>&nbsp;&nbsp;
  <a href="https://www.patreon.com/frenzypenguin_media"><img src="https://img.shields.io/badge/Patreon-frenzypenguin__media-F96854?logo=patreon&style=for-the-badge" alt="Support on Patreon"></a>
</p>
