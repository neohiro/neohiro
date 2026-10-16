# Repository Audit & Migration Plan — 2026-09-02

## Executive Summary

The neohiro ecosystem spans **4 GitHub orgs**, **~60 repositories**, and a complex
public-facing portfolio. Recent changes across the four repos show both progress
and significant architectural debt. This document audits the current state and
defines the migration path toward a centralized `private-assistant`.

---

## Part 1: State of the Four Target Repositories

### 1.1 `neohiro/neohiro` — Security portfolio anchor

**Purpose:** Primary public-facing landing for neohiro's security/privacy brand.
Published at `neohiro.github.io`.

**Current state (2026-09-02):**
- README is a simple text-only landing with links to other properties.
- The Jekyll site at `neohiro.github.io` (index.md) is feature-rich: typewriter
  hero, featured tools grid (from `_data/repos/`), hardening guides, community
  cards, FPM spotlight, privacy/TOS pages, consent flow, scroll animations.
- The README itself and the Jekyll site serve the same purpose — the README
  should be replaced with a proper badge/stats block pointing to the site.
- **Redundancy:** `neohiro/neohiro` README duplicates content from `neohiro/neohiro.github.io`.
  The README lives in the repo root; the site lives in `neohiro.github.io`.
  These should be clearly separated: README = code entry point + badges;
  Jekyll site = marketing surface.

**Issues found:**
- The README has no CodeQL badge, no license badge, no stars/fork counts
  (the template placeholder for GitHub stats is empty: `<p align="center">` is
  blank between the tags).
- No `CONTRIBUTING.md`, no structured issue templates (per batch_h.py work).
- Link to `transhumanists` is via GitHub Pages URL, not the actual org.

**Action items:**
- [ ] Add proper README badges: License, Python, CodeQL, GitHub stars.
- [ ] Ensure GitHub stats embed works (empty `<p align="center">` block).
- [ ] Create `CONTRIBUTING.md` with a development guide.
- [ ] Add structured issue templates (bug, feature, security).
- [ ] Clarify README vs site role: README = technical entry, site = marketing.

---

### 1.2 `neohiro/frenzypenguin-media` — Media + tools portfolio

**Purpose:** Secondary brand (FrenzyPenguin Media) focused on video/media content
plus a tools catalog. Published at `frenzypenguin-media.github.io`.

**Current state (2026-09-02):**
- README is a Liquid template stub with broken YAML frontmatter — it references
  `include` directives (`badges.html`, `heartbeat-status.html`) that are not
  self-contained. This is a Jekyll-includes template, not a standalone README.
- The actual content lives in `index.md` (Jekyll site) and `index-unified.html`.
- `repositories.md` is a full Jekyll page for the tools catalog.
- `media.md` is a video portfolio page.
- `_tools/` has 16 markdown tool descriptions (BlackGlass, HoneyScan, etc.)
  which feed into Jekyll's `_config.yml` collections.

**Redundancies:**
- `index.md` and `index-unified.html` both serve as the homepage. They are
  different: `index.md` is a proper Jekyll page; `index-unified.html` is a
  standalone HTML page. Only one should be `index.html`.
- `repositories.md` and the `_tools/` collection serve the same purpose.
  The `_tools/` collection is the source-of-truth (machine-readable), but
  `repositories.md` generates the HTML grid. These should be consolidated.
- `index-unified.html` duplicates all the content of `index.md`. It should be
  removed and `index.md` should be the canonical source.
- The README template is broken/incomplete — it needs to be replaced with a
  real README that points to the Jekyll site.

**Action items:**
- [ ] Replace broken README template with a proper standalone README.md that
  explains the repo, links to the GitHub Pages site, and has badges.
- [ ] Delete `index-unified.html` — it is redundant with `index.md`.
- [ ] Verify `repositories.md` is generated from `_tools/` (it reads from
  `site.tools` in Jekyll) — confirm this is working and remove manual duplication.
- [ ] Ensure `_config.yml` properly loads the `_tools/` collection.
- [ ] Add structured issue templates.
- [ ] Add CodeQL workflow if not present.

---

### 1.3 `neohiro/openstageisland.github.io` — Second Life music venue site

**Purpose:** Documentation/hub for the Open Stage Island Second Life destination.
Published at `neohiro.github.io/openstageisland.github.io/`.

**Current state (2026-09-02):**
- README is the same broken template as frenzypenguin-media (Liquid includes).
- The `index.md` is a well-crafted Jekyll page with hero image, SL teleport
  links, feature grid, location data, and a sister-sites carousel.
- `data.json` exists for programmatic data.
- `heartbeats/` directory exists (likely from the Heart framework).

**Redundancies:**
- README is a template stub — same issue as frenzypenguin-media.
- The sister-sites section in `index.md` links to:
  - `https://neohiro.github.io/` (neohiro)
  - `https://neohiro.github.io/frenzypenguin-media/` (fpm)
  - `https://transhumanists.github.io/` (transhumanists)
  - `https://neohiro.github.io/links-secret/` (links)
  These are all hardcoded. If sites move, this section needs updating.
- **NOTE:** `neohiro/openstage-island.github.io` (with a hyphen) also exists.
  This is a duplicate and should be merged/archived.
- The `openstageisland` org mentioned in the README (for the future openstageisland
  org) is not yet created — the README mentions "GitHub org creation pending".

**Action items:**
- [ ] Fix the README template (replace with real content).
- [ ] Archive `neohiro/openstage-island.github.io` (hyphen version) — it's
  clearly a duplicate.
- [ ] Update sister-sites section to use canonical URLs that are stable.
- [ ] Add structured issue templates.

---

### 1.4 `transhumanists/transhumanists` — Transhumanism content (MISSING)

**Status:** `neohiro/transhumanists` does not exist. The `transhumanists.github.io`
GitHub Pages site exists (referenced in `neohiro/neohiro` links and in the OSI
sister-sites), but there is no `neohiro/transhumanists` repo.

**What it should be:**
- A public GitHub Pages site (`transhumanists.github.io`) with transhumanism
  content, similar in structure to the FPM and OSI repos.
- It is referenced in the network but not yet materialized under the neohiro org.

**Action items:**
- [ ] Create `neohiro/transhumanists` repo with a proper README + Jekyll site
  matching the pattern of FPM and OSI repos.
- [ ] Add structured issue templates.
- [ ] Update all sister-sites references to point to the new canonical location.

---

## Part 2: Redundancy & Cleanup Analysis

### 2.1 Duplicate repo names

| Repo A | Repo B | Status |
|--------|--------|--------|
| `neohiro/openstageisland.github.io` | `neohiro/openstage-island.github.io` | Archive B (hyphen version) |
| `neohiro/neohiro.github.io` (index.md) | `neohiro/frenzypenguin-media/index.md` | OK — different brands |
| `neohiro/neohiro` README | `neohiro/neohiro.github.io/index.md` | OK — README = entry, site = marketing |
| `neohiro/wingman-hub` | `neohiro/private-assistant` | See § 3 |

### 2.2 Broken README templates

Both `frenzypenguin-media` and `openstageisland.github.io` have READMEs that are
Liquid template stubs (`<!-- TEMPLATE-SHARED:HEADER -->` etc.). These are
incomplete and not user-friendly. They need real README content.

### 2.3 Duplicate `index-unified.html`

`frenzypenguin-media/index-unified.html` (27KB) duplicates the content of
`index.md`. Delete it.

### 2.4 Local `repos/` vs GitHub repos drift

The local `repos/` directory has 27 subdirectories, but many are incomplete:
- `NewsAgreggator/` (note: misspelled — should be `NewsAggregator/`)
- Some dirs are very sparse (3 files, minimal content)

The local `batchA/` directory has release workflow files staged but not committed.
The `batchH/` has changelog/content updates staged but not committed.
The `batchI/` has release notes additions staged but not committed.

**Action items:**
- [ ] Audit local `repos/` dirs vs GitHub state — identify which need updating.
- [ ] Commit pending `batchH` (changelogs + CodeQL badges) and `batchI`
  (generate_release_notes) staged changes.
- [ ] Fix `NewsAgreggator` → `NewsAggregator` spelling.

---

## Part 3: private-assistant Migration Plan

### 3.1 Current Structure

`neohiro/private-assistant` is the canonical home, but its sub-components are
split across multiple repos:

| Repo | Role | Migrate into private-assistant? |
|------|------|-------------------------------|
| `neohiro/private-assistant` | Central hub — memory palace, userdata, ops | YES — root |
| `neohiro/Mouth` | Output layer — WhatsApp, web, social | YES — as `/Mouth` |
| `neohiro/Brain` | Intelligence hub — context, cognition | YES — as `/Brain` |
| `neohiro/Heart` | Cadence engine — scheduling, heartbeats | YES — as `/Heart` |
| `neohiro/doctor` | Self-healing diagnostics | YES — as `/doctor` |
| `neohiro/voicemail` | Multi-channel intake | YES — as `/voicemail` |
| `neohiro/wingman-hub` | **DEPRECATED** — replaced by private-assistant | Archive after migration |
| `neohiro/news` | RSS/HN aggregator | YES — as `/news` |
| `neohiro/worldmap` | Global data layers | YES — as `/worldmap` |
| `neohiro/network` | Device telemetry, health | YES — as `/network` |
| `neohiro/links` | Curated platform index | YES — as `/links` |
| `neohiro/userdata` | Encrypted user PII store | Already separate — keep as-is (private) |
| `neohiro/whatsapp-bridge` | WhatsApp intake channel | Merge into `/Mouth` or `/voicemail` |

### 3.2 Migration Phases

#### Phase 1: Tidy the four public repos (this week)
1. Fix broken README templates in frenzypenguin-media and openstageisland.
2. Delete `index-unified.html` from frenzypenguin-media.
3. Archive `openstage-island.github.io` (hyphen version).
4. Add structured issue templates to all public repos.
5. Commit pending `batchH` and `batchI` staged changes.
6. Create `neohiro/transhumanists` with proper README + Jekyll site.

#### Phase 2: Centralize private-assistant components (next sprint)
1. Design the new `private-assistant` directory structure:
   ```
   private-assistant/
     Mouth/          ← from neohiro/Mouth
     Brain/          ← from neohiro/Brain
     Heart/          ← from neohiro/Heart
     doctor/         ← from neohiro/doctor
     voicemail/      ← from neohiro/voicemail
     news/           ← from neohiro/news
     worldmap/       ← from neohiro/worldmap
     network/        ← from neohiro/network
     links/          ← from neohiro/links
     whatsapp-bridge/ ← merge into Mouth/voicemail
     userdata/       ← symlink or reference to neohiro/userdata
   ```
2. Update all internal `neohiro/Brain/_body/` references to point to new paths.
3. Update `neohiro/bootstrap/` to reference the new structure.
4. Update `neohiro/repo-audit/MIGRATION.md` with the new plan.
5. Archive `neohiro/wingman-hub` (deprecated, replaced by private-assistant).

#### Phase 3: Wire the body (after migration)
1. Update `Brain/REGISTRY.md` with new Heart steering paths.
2. Update `Heart/.neohiro/heart.yaml` to discover from `private-assistant`.
3. Update `network/WORKFLOWS.md` to reference new org layout.
4. Verify all scripts in `private-assistant/scripts/` still work with new paths.
5. Update `SPEC_ADDENDUM.md` wiring order.

#### Phase 4: Deprecate and clean up
1. Add DEPRECATED notices to `neohiro/wingman-hub`, `neohiro/Mouth`,
   `neohiro/Brain`, `neohiro/Heart`, `neohiro/doctor`, `neohiro/voicemail`.
2. After one full cycle of the new system, archive the old standalone repos.
3. Update all `neohiro/*` repo READMEs that reference the old paths.

### 3.3 Key Migration Risks

1. **Path dependencies:** Scripts in `private-assistant/scripts/` hardcode
   paths like `../Brain/`, `../Mouth/`. After moving these into subdirectories
   of `private-assistant`, paths become `Brain/`, `Mouth/`. Need a path
   migration script.
2. **Git history:** Migrating by moving files (not copying) preserves history.
   Use `git subtree add` or re-clone + push with `--follow` for each component.
3. **Render deployment:** `private-assistant/render.yaml` and `Mouth/Dockerfile`
   may have hardcoded image names. Update before migration.
4. **WhatsApp:** `whatsapp-bridge/` integrates with Mouth — ensure no breaking
   changes to webhook endpoints.

---

## Part 4: Interoperability & Dependencies

### 4.1 Cross-repo dependencies (from Brain/REGISTRY.md analysis)

```
neohiro/Brain
  ├── neohiro/Heart           (cadence engine)
  ├── neohiro/Mouth          (output layer)
  ├── neohiro/voicemail      (intake)
  ├── neohiro/userdata       (encrypted PII)
  ├── neohiro/links          (OSINT feeds)
  └── neohiro/network        (device telemetry)

neohiro/private-assistant
  ├── neohiro/Brain          (owning Brain)
  ├── neohiro/Mouth          (owning output)
  ├── neohiro/Heart         (cadence)
  ├── neohiro/userdata       (PII)
  └── neohiro/links-secret   (whitelisted redirects)

neohiro/Heart
  └── neohiro/links-secret   (visitor counter IDs, social counter keys)

neohiro/bootstrap
  └── (all of the above — orchestrates full body)
```

### 4.2 GitHub Pages / Jekyll site dependencies

Both `neohiro/neohiro.github.io` and `neohiro/frenzypenguin-media` use:
- `_config.yml` with collections (`tools/`)
- `_includes/` for shared components
- `_layouts/` for page templates
- `_data/` for structured data
- Jekyll plugins: jekyll-feed, jekyll-seo-tag, jekyll-sitemap

The `_tools/` collection in FPM is the machine-readable catalog. The Jekyll site
reads `site.tools` to generate the grids. This is the correct pattern — keep it.

### 4.3 Heart process architecture

Heart uses `.neohiro/heart.yaml` for per-org discovery. Each org has its own
Heart steering repo. After migration to `private-assistant`, the Heart discovery
mechanism should be updated to point to `private-assistant/Heart/`.

---

## Part 5: Recommended Immediate Actions (Priority Order)

1. **[HIGH]** Fix broken README templates in `frenzypenguin-media` and
   `openstageisland.github.io` — replace Liquid template stubs with real content.
2. **[HIGH]** Delete `frenzypenguin-media/index-unified.html` — redundant.
3. **[HIGH]** Archive `neohiro/openstage-island.github.io` (hyphen version).
4. **[HIGH]** Commit pending `batchH` and `batchI` staged workflow changes.
5. **[MEDIUM]** Create `neohiro/transhumanists` repo with Jekyll site + proper README.
6. **[MEDIUM]** Add structured issue templates to all public repos.
7. **[MEDIUM]** Add CodeQL workflow to repos that lack it.
8. **[MEDIUM]** Create `CONTRIBUTING.md` for flagship repos.
9. **[LOW]** Design `private-assistant/` directory structure for Phase 2 migration.
10. **[LOW]** Fix `NewsAgreggator` → `NewsAggregator` spelling.

---

## Part 6: Notes for OpenCode Agent

This document should be used as a runbook. The agent should:
- Before editing any file, read it first (required by the Edit tool).
- When fixing READMEs, preserve existing badges/stats and add missing ones.
- When deleting files, verify they are truly redundant first.
- When committing, use `gh repo list` to confirm current repo state.
- For the private-assistant migration, prefer `git subtree add` over copy-paste
  to preserve commit history.
- Always run `npm run lint` / `python -m py_compile` / etc. after code changes.
- Never commit secrets or API keys — check with `gh secret list` before pushing.

---

## Part 7: Additional Repos Audited — 2026-09-02 (voicemail, Mind, killswitch, monetization, network, userdata, bootstrap)

### 7.1 `neohiro/voicemail` — OpenCode workspace backup (MISNAMED)

**Contents:**
- `opencode-backup.ps1` — hourly cron backup of OpenCode state (config, auth, plugins, SQLite sessions DB, mobile-sync state)
- `opencode.config.jsonc` — main OpenCode agent config (model, port 4096, watcher ignores)
- `templates/` — OpenCode scaffold templates (agent-commands, llm-prompts, node-template, repo-templates, scaffold.sh, svg-templates, website-templates, tests/, _shared/)
- `repo-audit/` — MANUAL_MIGRATION.md, migrations.json, scripts/
- `.github/` — workflows

**Findings:**
- This repo is NOT a voicemail/intake system despite its name.
- It is an **OpenCode workspace backup and scaffold** system — it backs up the
  local OpenCode installation and provides project templates.
- `opencode-backup.ps1` backs up: config, auth tokens, plugins, SQLite sessions DB,
  and mobile-sync state — all pushed to `devices/<Device>/opencode-backup/` in Git.
- `neohiro/opencode-config` is a SEPARATE repo that handles device sync scripts
  and startup automation. These two overlap in purpose (both are OpenCode workspace
  management) but serve different layers.
- The repo has **NO README.md** — the repo description is the only documentation.

**Action items:**
- [ ] Rename to `neohiro/opencode-workspace` (or similar) to reflect actual purpose.
- [ ] Create `README.md` explaining it backs up the OpenCode desktop installation.
- [ ] Move `repo-audit/` into `neohiro/repo-audit` (already exists).
- [ ] Decide: merge with `neohiro/opencode-config` or keep separate?
  - Keep separate if: backup (voicemail) vs. device sync (opencode-config) is intentional split
  - Merge if: both are workspace management and should be one repo

**Contents:**
- `.github/` — workflows
- `repo-audit/` — MANUAL_MIGRATION.md, migrations.json, scripts/
- `templates/` — OpenCode scaffold templates (agent-commands, llm-prompts, node-template, repo-templates, scaffold.sh, svg-templates, website-templates, tests/, _shared/)
- `opencode-backup.ps1` — OpenCode workspace backup script
- `opencode.config.jsonc` — OpenCode per-device agent config

**Findings:**
- This repo is primarily an **OpenCode workspace scaffold** — it holds the
  OpenCode agent config, templates, and backup scripts. The "voicemail" name is
  misleading; the actual voicemail functionality (multi-channel intake) may be
  represented by the templates, but the source code doesn't exist here.
- The `repo-audit/` subdirectory suggests it was used to audit other repos.
- **Redundancy with `private-assistant`:**
  - `private-assistant/channels/` already has channel intake code
  - `private-assistant/templates/` has report templates
  - `private-assistant/scripts/` has intake processing scripts
- The `templates/` directory (OpenCode scaffolding) does NOT belong in
  `private-assistant` — it's an OpenCode agent config, not private-assistant data.

**Action items:**
- [ ] Clarify what "voicemail" means: intake + triage + brain handoff, or OpenCode backup?
- [ ] If it's OpenCode scaffolding, consider moving it into `neohiro/opencode-config`
  or keeping it as `neohiro/voicemail` (current name is misleading).
- [ ] Move `repo-audit/` into `neohiro/repo-audit` (already exists).
- [ ] Merge `templates/` OpenCode scaffolding into `neohiro/opencode-config` if appropriate.
- [ ] Create proper README.md — currently NONE exists.

---

### 7.2 `neohiro/Mind` — Proprioception and self-reflection (VERY SPARSE)

**Contents:**
- `src/mind/` — `__init__.py`, `analyze_trends.py`, `feedback_signals.py`, `improve.py`, `ponder.py`, `reflect_on_output.py`
- `Reminders/20_mind_trends.sh` — reminder for running trends analysis
- `.github/`, `.gitignore`, `CODE_OF_CONDUCT.md`, `CREDITS.md`, `README.md`, `SECURITY.md`, `pyproject.toml`, `tests/`

**Findings:**
- Mind is a **4th organ** alongside Brain/Heart/Mouth — responsible for
  self-reflection ("how did my decisions turn out?") and pattern recognition.
- Very minimal codebase — 6 Python files in `src/mind/`.
- Mind is mentioned in the private-assistant body diagram but is the least
  developed of the four organs.
- The `Reminders/` file suggests this is still being actively developed.

**Relationship to private-assistant:**
- voicemail has NO relation to private-assistant — it's an OpenCode workspace tool.
- For intake/triage of messages, see `private-assistant/channels/` and `Mouth/`.
- The `templates/` OpenCode scaffolding does NOT belong in `private-assistant` —
  it's an OpenCode agent config, not private-assistant data.
Mind and Brain are closely related — Mind reviews Brain's decisions. They should
stay as separate repos but share a discovery mechanism (both have `.neohiro/` manifests).

**Action items:**
- [ ] Add Mind as `/Mind` under `private-assistant` in Phase 2 migration.
- [ ] Wire Mind into Brain's decision review pipeline.
- [ ] Create `Mind/.neohiro/mind.yaml` for Heart discovery (following Heart's pattern).
- [ ] Consider merging Mind's `src/` into Brain's `_body/mind/` if they share runtime.

---

### 7.3 `neohiro/killswitch` — Godadmin emergency stop

**Contents:**
- `src/` — emergency stop logic (no file listing available)
- `.github/`, `CODE_OF_CONDUCT.md`, `CREDITS.md`, `README.md`, `SECURITY.md`

**Findings:**
- Public README explains the killswitch concept clearly.
- It's a **cross-cutting concern** — affects ALL organs (Brain, Heart, Mouth,
  Voicemail, News, etc.) when armed.
- Should NOT be merged INTO private-assistant — it needs to remain independently
  deployable since it must be able to shut down the entire stack including the
  private-assistant itself.

**Action items:**
- [ ] Keep `neohiro/killswitch` as a standalone repo.
- [ ] Update `network/WORKFLOWS.md` to include killswitch in the body map.
- [ ] Ensure killswitch is in `neohiro/bootstrap` install list.
- [ ] Create `killswitch/.neohiro/killswitch.yaml` manifest for body discovery.

---

### 7.4 `neohiro/monetization` — Revenue tracking (read by Brain)

**Contents:**
- `data/` — sponsors.json, api_quotas.json, affiliate.json, billing_history.json, alerts.json
- `svg/` — 3-tier SVG cards (public / authed / godadmin)
- `scripts/` — track.py, billing_summary.py
- `.github/`, `.gitignore`, `CODE_OF_CONDUCT.md`, `CREDITS.md`, `MIGRATIONS.md`, `README.md`, `SECURITY.md`

**Findings:**
- Public README describes it as the body's "metabolism" — tracks revenue and costs.
- Brain reads it for financial health decisions (read-only from Brain's perspective).
- Never reads user data — clean separation.
- Has its own SVG card generation for dashboards.

**Action items:**
- [ ] Add as `/monetization` under `private-assistant` in Phase 2 migration.
- [ ] Update `network/WORKFLOWS.md` to include monetization in the body map.
- [ ] Ensure monetization SVG cards are referenced in the dashboard.

---

### 7.5 `neohiro/network` — Central nervous system (LARGE)

**Contents:**
- `__init__.py`, `schema_validator.py`, `conventions_validator.py`
- `schemas/` — data schemas
- `metrics/` — per-device rolling metrics
- `brain_client/` — Brain integration client
- `cmd/` — CLI commands
- `svg/` — generated SVG cards
- `scripts/` — bootstrap.sh, brain-node.sh, generate-svg.js, heartbeat-sidecar.sh, heart_dependabot_scope.py, dependabot_aggregator.py, install-brain-node.sh
- `public/`, `authed/` — visibility-tiered output
- `.github/`, `.pre-commit-hooks.yaml`, `Dockerfile`, `CONVENTIONS.md`, `SCHEMA.md`, `SPEC_HUB.md`, `SPEC_ADDENDA.md`, `WORKFLOWS.md`, `action.yml`, `entrypoint.sh`

**Findings:**
- This is the **largest and most complex** infrastructure repo.
- `WORKFLOWS.md` is the canonical body map (all 4 orgs: neohiro, frenzypenguin-media, openstageisland, transhumanists).
- `CONVENTIONS.md` defines cross-repo naming/data conventions.
- All other organs feed telemetry into network — it's the observability backbone.
- `brain_client/` connects to Brain for decision events.
- `heartbeat-sidecar.sh` — Heart integration.

**Relationship to private-assistant:**
- Network feeds into Brain (decision telemetry)
- Network receives from Heart, iot, news, tailscale-exit
- Should NOT be merged into private-assistant — it's a cross-cutting
  infrastructure concern that spans multiple orgs.

**Action items:**
- [ ] Keep `neohiro/network` as a standalone cross-org infrastructure repo.
- [ ] Update `network/WORKFLOWS.md` with the new private-assistant structure.
- [ ] Add network to `neohiro/bootstrap` install list (already there per bootstrap README).
- [ ] Create `network/.neohiro/network.yaml` manifest for body discovery.

---

### 7.6 `neohiro/userdata` — Encrypted PII store

**Contents:**
- `src/` — age_cli.py, access_enforcer.py
- `data/` — per-user encrypted PII (profile.yaml.age, memory.md.age, episodes.md.age, interests.md.age, hearsay/, whatsapp/)
- `wout/` — encrypted user data for the godadmin
- `PHILOSOPHY.md` — privacy design rationale
- `.github/`, `.gitignore`, `CODE_OF_CONDUCT.md`, `CREDITS.md`, `MIGRATION.md`, `README.md`, `SECURITY.md`

**Findings:**
- Already **the canonical userdata store** for the entire ecosystem.
- `private-assistant/README.md` explicitly points to `neohiro/userdata` as the
  canonical home for all user PII.
- Uses `age` encryption (age-cli.py) with user + godadmin as recipients.
- Clearly should remain SEPARATE from private-assistant — PII must be in its own
  isolated repo.

**Action items:**
- [ ] Keep `neohiro/userdata` as a SEPARATE private repo — do NOT migrate.
- [ ] Ensure `private-assistant/userdata/` stub points to `neohiro/userdata`.
- [ ] Document the access pattern in `private-assistant/docs/USERDATA_ACCESS.md`.

---

### 7.7 `neohiro/bootstrap` — One-command body installer

**Contents:**
- `install.sh` — the main installer
- `migration-controller.py` — migration orchestration
- `cloud-runner-agent.py` — CI/CD integration
- `pa-bridge.sh` — private-assistant bridge
- `heart-guard.yml` — Heart monitoring config
- `healthz-monitor.py` — health check monitor
- `protect-repos.sh` — repo protection script
- `.github/`, `.gitignore`, `CODE_OF_CONDUCT.md`, `CREDITS.md`, `README.md`, `SECURITY.md`, `tests/`

**Findings:**
- Installs: Brain, Heart, Mouth, Mind, userdata, iot, network, news, tailscale-exit, monetization.
- After the migration, bootstrap needs to be updated to install from the new
  `private-assistant` structure instead of individual repos.
- `pa-bridge.sh` already exists — suggests bootstrap is already aware of the
  private-assistant migration.

**Action items:**
- [ ] Add as `/bootstrap` under `private-assistant` in Phase 2 migration.
- [ ] Update `install.sh` to clone/mount private-assistant subdirectories.
- [ ] Update `pa-bridge.sh` to reference new paths inside private-assistant.
- [ ] After migration, deprecate `neohiro/bootstrap` standalone repo.

---

## Part 8: Complete Migration Map — Revised

### 8.1 What's IN private-assistant (centralize)

| Component | From repo | New path under private-assistant/ |
|-----------|-----------|----------------------------------|
| Core intelligence | neohiro/Brain | Brain/ |
| Cadence engine | neohiro/Heart | Heart/ |
| Output layer | neohiro/Mouth | Mouth/ |
| Self-reflection | neohiro/Mind | Mind/ |
| Diagnostics | neohiro/doctor | doctor/ |
| Intake/triage | neohiro/voicemail | voicemail/ |
| RSS/HN feeds | neohiro/news | news/ |
| Data layers | neohiro/worldmap | worldmap/ |
| Platform index | neohiro/links | links/ |
| Revenue tracking | neohiro/monetization | monetization/ |
| Installer | neohiro/bootstrap | bootstrap/ |
| Cross-org network | neohiro/network | network/ |
| WhatsApp bridge | neohiro/whatsapp-bridge | whatsapp-bridge/ |

### 8.2 What's STAYING SEPARATE (don't migrate)

| Repo | Reason |
|------|--------|
| neohiro/userdata | Encrypted PII — must remain isolated |
| neohiro/killswitch | Cross-cutting emergency stop — must be independently deployable |
| neohiro/links-secret | Secrets vault — must be separately secured |
| neohiro/bootstrap | (migrate into private-assistant, deprecate standalone) |
| neohiro/opencode-config | OpenCode agent config — not private-assistant data |
| neohiro/repo-audit | Audit runbook — belongs in this repo |

### 8.3 Phase 2 migration order

**Step 1:** Design `private-assistant/` directory structure (this document)
**Step 2:** Clone all source repos into local `private-assistant/` staging dir
**Step 3:** Use `git subtree add` to bring each component in (preserves history)
**Step 4:** Update all import/path references in scripts
**Step 5:** Update `bootstrap/install.sh` to point to new structure
**Step 6:** Update `network/WORKFLOWS.md` to reflect new paths
**Step 7:** Update Heart's `.neohiro/heart.yaml` registry path
**Step 8:** Create `private-assistant/.neohiro/body.yaml` manifest
**Step 9:** Verify all scripts in `scripts/` with new paths
**Step 10:** Deprecate old standalone repos (add DEPRECATED.md, archive after 1 cycle)

### 8.4 Target private-assistant/ directory structure

```
private-assistant/
├── .github/                  # shared workflows, issue templates
├── .neohiro/                 # body discovery manifests
│   ├── body.yaml              # master manifest: all organs, roles, dependencies
│   ├── heart.yaml             # Heart discovery override
│   ├── brain.yaml             # Brain discovery
│   └── kill_switch.yaml       # killswitch integration
├── Brain/                    # from neohiro/Brain (intelligence hub)
│   ├── _body/                 # organ discovery
│   ├── _entities/             # entity definitions
│   ├── _schema/               # data schemas
│   ├── _tools/                # tools registry
│   ├── Heart/                 # Heart subcomponent
│   ├── knowledge/             # knowledge base
│   ├── requirements.txt
│   └── ...
├── Heart/                    # from neohiro/Heart (cadence engine)
│   ├── .neohiro/heart.yaml   # org override
│   ├── schedules/REGISTRY.yaml
│   ├── tools/                 # heartbeat populators
│   └── ...
├── Mouth/                    # from neohiro/Mouth (output layer)
│   ├── src/
│   ├── docker/
│   └── ...
├── Mind/                     # from neohiro/Mind (self-reflection)
│   └── src/mind/
├── doctor/                   # from neohiro/doctor (self-healing)
├── voicemail/                # from neohiro/voicemail (intake/triage)
├── network/                  # from neohiro/network (nervous system)
│   ├── metrics/              # per-device telemetry
│   ├── svg/                  # status cards
│   └── scripts/
├── news/                     # from neohiro/news
├── worldmap/                 # from neohiro/worldmap
├── links/                    # from neohiro/links
├── monetization/             # from neohiro/monetization
├── whatsapp-bridge/          # from neohiro/whatsapp-bridge
├── bootstrap/                # from neohiro/bootstrap
├── render.yaml               # Render deployment config
├── SPEC.md                   # master system specification
├── SPEC_ADDENDUM.md          # gap analysis
├── MIGRATION.md              # this migration plan
├── README.md                 # entry point
├── SECURITY.md
├── PRIVACY_POLICY.md
├── TERMS_OF_SERVICE.md
├── scripts/                  # shared operational scripts
├── data/                     # operational data (encrypted vaults, metrics)
├── memory/                   # working memory (public-safe subset)
├── templates/                # report/briefing templates
├── config/                   # shared LLM config, rules, schedules
├── intelligence/             # agent map, commands, triage prompts
├── backups/                  # backup snapshots
├── recovery/                 # recovery procedures
├── logs/                    # operational logs
├── userdata/                 # STUB → points to neohiro/userdata
└── tests/
```

### 8.5 Critical path dependencies (must be updated during migration)

1. `Brain/_body/` references → `Brain/`, `Heart/`, `Mouth/`, `Mind/`, `userdata/`
2. `Heart/schedules/REGISTRY.yaml` → `Brain/`, `Mouth/`, `network/`, `news/`, `links/`
3. `bootstrap/install.sh` → all organ repos
4. `bootstrap/pa-bridge.sh` → `Brain/`, `Mouth/`, `Heart/`
5. `network/scripts/brain-node.sh` → `Brain/`
6. `network/brain_client/` → `Brain/` API
7. All scripts in `private-assistant/scripts/` → `Brain/`, `Mouth/`, `Heart/`
8. `render.yaml` → service names, image names
9. `Heart/.neohiro/heart.yaml` → `Heart/`
10. `network/WORKFLOWS.md` → body map with all orgs

---

## 9. Self-improvement follow-ups (2026-09-02)

After the bulk migration work, the following code-quality cleanups were applied
via small focused PRs.

### 9.1 `neohiro/private-assistant`

- **`scripts/scan_open_items.py`** — removed unused `import os`; extracted
  magic number `280` to `BODY_PREVIEW_LEN`; added `.git` guards to both
  `**/*.md` and `*.json` glob patterns; gated `stdout`/`stderr` UTF-8
  rewrap to `sys.platform == "win32"` (CI runs on Linux, so the wrapper
  was a no-op but misleading). (PR #12)
- **`.github/workflows/daily-open-items.yml`** — dropped unused
  `pip install requests` (script uses stdlib only); fixed broken
  `Send WhatsApp Alert on Failure` step where `env:` was indented inside
  `run: |` (making it a shell command, not a YAML mapping — alerts were
  silently never delivered on failure); added `concurrency: group:
  open-items-scan` to prevent overlapping scheduled + dispatch runs from
  stomping each other's pushes.

### 9.2 `neohiro/openstageisland.github.io`

- **`_layouts/default.html`** — dropped redundant `type="text/javascript"`
  attribute (HTML5 default). No behavior change. (PR #5)
- **Added `CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1, matching
  frenzypenguin-media. (PR #5 — supersedes PR #3/#4 which were closed)
- **Note on Pages URL:** The site is deployed as a subfolder under
  `neohiro.github.io/openstageisland.github.io/` (verified via GitHub Pages
  API). The direct `openstageisland.github.io` hostname returns 404 because
  no CNAME is configured. This is correct for a subfolder deploy and not
  a misconfiguration.
- **`_config.yml`** — added missing
  `plugins: [jekyll-seo-tag]`; the layout used `{% seo %}` but the gem
  was not declared, so it silently emitted nothing on every page. (PR #5)
- **`_layouts/default.html`** — dropped duplicate manual
  `<title>`, `<meta name="description">`, `<meta name="author">` above
  `{% seo %}`; kept `<link rel="canonical">` with the page-level override.
  (PR #5)
- **`_includes/org-profile.html`** — fixed stale descriptions:
  FPM still said "indie media studio" (should be "security hardening &
  privacy tools"); transhumanists said "tracking human progress" (should be
  "human enhancement"). (PR #5)
- **`index.md`** — fixed broken `/README/` link (README.md
  is excluded from Jekyll builds; the URL 404'd). Changed to a GitHub
  source link. (PR #5)
- **`.github/workflows/ci.yml` + new `Gemfile`** — the
  workflow validated source files but deployed without running Jekyll. The
  deploy step uploaded the raw repo as a Pages artifact; GitHub Pages then
  built it server-side. This meant CI couldn't catch Jekyll build errors.
  Now builds locally via `bundle exec jekyll build` and uploads `_site/`.
  (PR #6)
- **`Gemfile`** — pins Jekyll 4.4, jekyll-seo-tag, kramdown-parser-gfm,
  jekyll-sitemap with pessimistic version constraints (`~> X.Y.0`) so CI
  has consistent gem versions across runs. (PR #6)

### 9.3 `neohiro/transhumanists`

- **Removed dead CSS** — `.reveal` and `.reveal-in` rules in `style.css` were
  defined but never applied to any HTML element and had no JS to trigger them.
  (PR #4 — supersedes PR #3 which was closed)
- **Added `CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1, matching
  sister repos. (PR #4)
- **`_config.yml`** — corrected typo
  `syntax_highighlighter` → `syntax_highlighter` (Rouge syntax highlighting
  was silently disabled). (PR #5)
- **`_layouts/default.html`** — canonical link previously used
  `{% if page.canonical %}` which never rendered since no page set that front
  matter. Now uses `page.canonical | default: site.url` (matching OSI/FPM
  pattern). Added missing `og:url` to the hand-rolled OG tags. Added
  `default:` filters for robustness. (PR #5)

### 9.4 `neohiro/frenzypenguin-media`

- **`_config.yml`** — fixed `github_repo` mismatch: value
  was `frenzypenguin-media.github.io` (Pages hostname) but the actual repo
  is `frenzypenguin-media`. With the wrong value, `site.github.*` template
  variables resolve to a 404 URL. (PR #8)
- **`_layouts/default.html`** — dropped deprecated
  `align="center"` (replaced with `style="text-align: center;"`);
  dropped `type="text/javascript"` from script tag; added
  `color-scheme: light dark` meta tag for proper dark-mode browser
  UI rendering. (PR #8)

### 9.5 `neohiro/neohiro`

- **`.github/workflows/reusable-readme-drift.yml`** (audit pass) — fixed
  script path from `neohiro/readme_drift.py` to `readme_drift.py`. The
  workflow checks out the repo at `${{ inputs.workspace }}`, so the script
  is at `$workspace/readme_drift.py` (repo root), not
  `$workspace/neohiro/readme_drift.py`. The old path would have caused
  `FileNotFoundError` for any caller of this reusable workflow.

---

## 10. Principal-engineer audit findings — not fixed this session

Issues found during the 2026-09-02 self-improvement pass that were assessed
as higher-risk or larger-scope changes. Documenting for future attention.

### Critical — not fixed (risk assessment: too large for single-PR)

- **`scan_open_items.py` silent dedupe history loss on corrupt `known_items.json`** —
  if `known_items.json` is truncated mid-write, `load_known()` returns an
  empty dict and the next run re-queues all ~21 historical items. Combined
  with non-atomic `write_text` writes, this creates a data-integrity race.
  Fix: back up corrupt file, exit non-zero, use `os.replace()` for atomicity.
  **Risk: silent re-queue flood on disk-full or git-push race.**

- **`data/outbox/` in `scan_open_items.py` creates outbound alerts as "open
  items"** — the outbox is where outbound WhatsApp messages are stored.
  Every sent alert becomes a new "open item" on the next scan, flooding
  the queue. Remove `"outbox"` from the scan sources or filter by status.
  **Risk: queue noise; also amplifies PII-in-git issue.**

- **`data/processed_strangers/` silently produces 0 candidates** — the
  webhook payload shape is `{"entry": [...]}` not `{"items": [...]}`.
  The scan checks `payload.get("items")` which is always `None` for these
  files. Either the scan was never updated for the actual payload, or the
  source should be removed. **Risk: wrong dedupe, silent 0-candidate output.**

- **All `data/processed_*` content committed to a public repo** — the
  scan writes full WhatsApp message bodies (including sender phone numbers,
  `@lid` identifiers, and free text) into `data/pending/<date>/items.json`,
  then `git add data/pending/ data/open_items_history/` commits them to a
  public repo. **Risk: PII leakage via git history.**

### High — not fixed

- **`git pull --rebase -X theirs` in `daily-open-items.yml` commit step** —
  on conflict, `-X theirs` silently discards the local (scheduled) commit's
  changes. Combined with the missing concurrency guard (now fixed), two
  overlapping runs could lose queued items. **Risk: silent data loss on
  schedule+dispatch overlap.**

- **`scan_open_items.py` writes `known_items.json` AFTER `items.json`** —
  if `save_known()` fails after `items.json` is written, items exist on
  disk but not in dedupe state → re-queued forever on next run. Should
  write `known_items.json` first so the failure mode is "dedupe says
  queued but file missing" (re-run idempotent).

- **`body` field from `processed_*` has no length cap** — `BODY_PREVIEW_LEN`
  only applies to reports. WhatsApp messages can be 65k chars; unbounded
  body is written to git. **Risk: repo bloat + PII amplification.**

- **`breach_monitor.py` sends plaintext email addresses in WhatsApp alert**
  — `f"🔒 New breach for {email}:"` exposes PII. Should redact to
  `n***@gmail.com`.

### Medium — not fixed

- **Action version pins** — `actions/checkout@v5`, `@v7` used without SHA pin.
  `actions/setup-python@v7` also unpinned. Add SHA pins for supply-chain
  integrity.
- **`pip install` with no hash verification** — if `requests` were still
  needed, `pip install requests` without `--require-hashes` allows a
  compromised PyPI mirror to serve malicious code.
- **18 includes are byte-for-byte identical between OSI and FPM** — a bug
  fixed in one repo won't propagate to the other. Consider a shared
  `neohiro/jekyll-includes` repo or at minimum a CI check that compares
  hashes.
- **`scan_open_items.py` uses full SHA-256 of `text.encode("replace")` truncated
  to 12 hex chars** — 48-bit fingerprint space. Two different items with
  same `sub`, `path.name`, and `title` will silently collide. Unlikely
  in practice but documented.
- **`data/known_items.json` (root) vs `data/open_items_history/known_items.json`
  duplicate** — both exist; only the latter is committed. The root one is
  never cleaned up. Pick one canonical location.
- **`data/processed_whatsapp/` schema inconsistency** — scripts write
  `{"phone":...}`, `{"to":...}`, and `{"number":...}` to the same directory.
  The Render consumer must handle all three. Verify.
- **FPM `pages.yml` vs OSI `ci.yml` action versions differ** — FPM uses
  `actions/upload-pages-artifact@v5`, OSI uses `@v4`. Standardize.
- **`transhumanists` GitHub Pages site is in `transhumanists/` org, not
  `neohiro/`** — `neohiro/transhumanists` is a separate scaffold.
  The live site at `transhumanists.github.io` is owned by the `transhumanists`
  GitHub org, not the `neohiro` org. Verify this is intentional.
- **`scan_open_items.py` outbox scan does not filter by status** — all outbox
  files (sent, failed, pending) are queued. Should filter to `status=pending`.
