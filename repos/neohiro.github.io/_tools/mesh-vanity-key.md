---
name: mesh-vanity-key
title: Mesh Vanity Key Generator
tagline: "Browser-based Ed25519 vanity key generator for mesh networks — MeshCore device keys, Meshtastic channel PSKs and node IDs"
platform: Web (GitHub Pages)
language: Python / JavaScript
category: Cryptography
featured: true
weight: 5
repo_url: https://github.com/neohiro/mesh-vanity-key
demo_url: https://neohiro.github.io/mesh-vanity-key/
stars: 0
forks: 0
open_issues: 0
created_at: 2026-09-29T20:48:19Z
pushed_at: 2026-09-30T09:48:42Z
icon: |
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0110 0v4"/>
  </svg>
---

**Mesh Vanity Key Generator** is a browser-based, GPU-accelerated Ed25519 vanity key generator for mesh networks: MeshCore device keys, Meshtastic channel PSKs and `!node` IDs, plus any other encoded public key you need to match against a pattern.

## Features
- **GPU-Powered (WebGPU)**: Parallel search across thousands of shader threads.
- **Zero Telemetry**: All key derivation runs 100% locally in your browser memory.
- **Scalar-Walk Optimized**: Faster prefix and suffix matching without CPU locking.
