# PROJECT_PLAN.md — neohiro/private-assistant

> **Status:** Planning | **Created:** 2026-09-04 | **Version:** 1.0

---

## 1. Executive Summary

**Vision:** Build the ultimate AI private assistant — a self-aware, multi-modal intelligence hub
that serves as a digital butler for authorized users (admin, godadmin). The system consumes global
news/OSINT feeds, manages social media, handles task automation, and continuously self-improves.

**Current State:**
- `neohiro/private-assistant` exists but is **NOT YET CREATED** on GitHub (404)
- Components exist as **standalone repos**: Brain, Heart, Mouth, Mind, doctor, voicemail, news,
  network, worldmap, links, monetization, bootstrap
- Most body organs are **archived** or incomplete
- No unified bootstrap exists

**Target State:**
- Single `neohiro/private-assistant` repo containing all intelligence modules
- One-command bootstrap with Docker isolation
- Full heartbeat → brain pipeline
- Secure networking via Tailscale exit-node
- Self-healing, self-improving autonomous operation

---

## 2. Repository Architecture

### 2.1 Target Directory Structure

```
private-assistant/
├── .github/                        # shared workflows, issue templates, CODEOWNERS
├── .neohiro/                      # body discovery manifests
│   ├── body.yaml                   # master manifest: all organs, roles, deps
│   ├── heart.yaml                 # Heart discovery override
│   ├── brain.yaml                  # Brain discovery
│   └── killswitch.yaml             # killswitch integration
│
├── Brain/                          # Intelligence hub
│   ├── _body/                      # organ discovery + communication
│   ├── _entities/                  # entity definitions (users, contexts)
│   ├── _schema/                    # data schemas (validated by network)
│   ├── _tools/                     # tools registry
│   ├── _intelligence/              # cognition, reasoning, planning
│   ├── _memory/                    # episodic + semantic memory
│   ├── _context/                   # situational awareness
│   ├── requirements.txt
│   └── README.md
│
├── Heart/                          # Cadence engine (scheduling)
│   ├── .neohiro/heart.yaml        # org override
│   ├── schedules/REGISTRY.yaml    # all scheduled jobs
│   ├── tools/                      # heartbeat populators (from neohiro/Heart)
│   └── README.md
│
├── Mouth/                          # Output layer
│   ├── src/                        # output generation
│   ├── channels/                   # WhatsApp, email, social, web
│   ├── docker/                     # Docker configs
│   └── README.md
│
├── Mind/                           # Self-reflection (proprioception)
│   ├── src/mind/
│   │   ├── analyze_trends.py
│   │   ├── feedback_signals.py
│   │   ├── improve.py
│   │   ├── ponder.py
│   │   └── reflect_on_output.py
│   └── README.md
│
├── doctor/                         # Self-healing diagnostics
│   ├── src/
│   ├── monitors/
│   └── README.md
│
├── voicemail/                      # Multi-channel intake + triage
│   ├── channels/
│   ├── triage/
│   └── README.md
│
├── network/                        # Nervous system (telemetry backbone)
│   ├── metrics/                    # per-device rolling metrics
│   ├── svg/                        # generated status cards
│   ├── brain_client/               # Brain integration
│   ├── scripts/
│   │   ├── bootstrap.sh
│   │   ├── brain-node.sh
│   │   ├── heartbeat-sidecar.sh
│   │   └── install-brain-node.sh
│   ├── schemas/
│   ├── CONVENTIONS.md
│   ├── SCHEMA.md
│   ├── WORKFLOWS.md
│   └── README.md
│
├── news/                           # RSS/HN aggregator (eyes)
│   ├── src/news/
│   │   └── sources/
│   ├── public/
│   ├── scripts/
│   └── README.md
│
├── worldmap/                       # Global data layers
│   └── README.md
│
├── links/                          # Curated platform index
│   └── README.md
│
├── monetization/                   # Revenue tracking (metabolism)
│   ├── data/
│   ├── svg/
│   ├── scripts/
│   └── README.md
│
├── whatsapp-bridge/                # WhatsApp intake
│   └── README.md
│
├── bootstrap/                      # One-command installer
│   ├── install.sh                  # main installer
│   ├── migration-controller.py
│   ├── cloud-runner-agent.py
│   ├── pa-bridge.sh
│   ├── heart-guard.yml
│   ├── healthz-monitor.py
│   ├── protect-repos.sh
│   └── README.md
│
├── config/                         # shared configuration
│   ├── llm.yaml                    # LLM router config, model priorities
│   ├── rules.yaml                  # operational rules
│   └── heartbeat.yaml              # heartbeat intervals
│
├── scripts/                        # shared operational scripts
│   └── scan_open_items.py
│
├── data/                           # operational data (encrypted vaults, metrics)
│
├── memory/                         # working memory (public-safe subset)
│
├── templates/                      # report/briefing templates
│
├── intelligence/                   # agent map, commands, triage prompts
│
├── backups/                        # backup snapshots
│
├── recovery/                      # recovery procedures
│
├── logs/                           # operational logs
│
├── userdata/                       # STUB → points to neohiro/userdata
│
├── tests/                          # shared test suite
│
├── render.yaml                     # Render deployment config
├── docker-compose.yml              # local development
├── Dockerfile                      # main container
├── SPEC.md                         # master system specification
├── SPEC_ADDENDUM.md               # gap analysis
├── MIGRATION.md                    # migration runbook
├── README.md                       # entry point
├── SECURITY.md
├── PRIVACY_POLICY.md
└── TERMS_OF_SERVICE.md
```

---

## 3. Module Definitions

### 3.1 Brain — Intelligence Hub

**Purpose:** Central cognition engine. Receives inputs, maintains context, makes decisions,
delegates to tools, generates responses.

**Responsibilities:**
- LLM router (OpenAI, Anthropic, Ollama, OpenRouter fallback chain)
- Context manager (conversation history, user preferences, global awareness)
- Tool orchestrator (calls Mouth, news, links, network as needed)
- Decision engine (autonomous task execution within permission bounds)
- Self-awareness loop (monitors own performance)

**Interfaces:**
- Input: voicemail (intake), news (world awareness), network (health), userdata (preferences)
- Output: Mouth (responses), doctor (self-reports), network (telemetry)

**Key Files:**
- `Brain/_intelligence/` — reasoning engines
- `Brain/_memory/` — episodic + semantic stores
- `Brain/_context/` — situational awareness

### 3.2 Heart — Cadence Engine

**Purpose:** Scheduling backbone. Runs heartbeats, triggers schedules, manages cron jobs.

**Responsibilities:**
- Heartbeat generation (regular health pings to all organs)
- Schedule execution (per REGISTRY.yaml)
- Failure detection and doctor escalation
- Cross-organ coordination

**Interfaces:**
- Reads: REGISTRY.yaml, all organ health endpoints
- Writes: schedule outputs, escalation triggers

**Key Files:**
- `Heart/schedules/REGISTRY.yaml` — master schedule manifest
- `Heart/tools/` — heartbeat populator scripts

### 3.3 Mouth — Output Layer

**Purpose:** All outbound communication. Generates and delivers responses.

**Responsibilities:**
- WhatsApp message delivery (Baileys)
- Email sending
- Social media posting (Twitter, Mastodon, Bluesky)
- Webhook responses
- Media generation

**Interfaces:**
- Input: Brain (content to deliver)
- Output: WhatsApp, email, social APIs, webhooks

**Key Files:**
- `Mouth/channels/` — per-channel implementations
- `Mouth/docker/` — Baileys + WhatsApp container

### 3.4 Mind — Self-Reflection

**Purpose:** Proprioception. Reviews Brain's decisions, identifies patterns, suggests improvements.

**Responsibilities:**
- Feedback signal analysis
- Trend detection in outputs
- Self-improvement recommendations
- Output quality review

**Interfaces:**
- Input: Brain decisions + outcomes
- Output: improvement recommendations to Brain

### 3.5 doctor — Self-Healing

**Purpose:** Diagnostics and auto-repair.

**Responsibilities:**
- Health monitoring across all organs
- Automatic restart on failure
- Escalation to godadmin on unrecoverable issues
- Runbook execution for known failure modes

### 3.6 voicemail — Intake

**Purpose:** Multi-channel message intake and triage.

**Responsibilities:**
- WhatsApp webhook reception
- Email ingestion
- API endpoint for direct messages
- Triage routing to Brain

---

## 4. Data Architecture

### 4.1 Databases

| Store | Technology | Purpose |
|-------|-----------|---------|
| Primary | PostgreSQL | User data, sessions, entities, contexts |
| Cache | Redis | Hot cache, session state, rate limiting |
| Memory | SQLite | Local working memory, ephemeral contexts |
| Encrypted | age-encrypted files | PII, secrets (in neohiro/userdata) |

### 4.2 Data Flow

```
news/ (eyes) ──────►                    ◄─── Mouth/ (mouth)
                         │
                    ┌──► Brain/ ◄───────┤
                    │    │              │
                    │    ├──► doctor/ ──┤
                    │    │              │
                    │    ├──► network/ │
                    │    │              │
Heart/ ◄────────────┤    │              │
(schedules)         │    │              │
                    │    └──► voicemail/
                    │         (intake) ◄───┐
                    │                      │
                    └──────────────────────┘
                           (closed loop)
```

---

## 5. Security Architecture

### 5.1 Network Isolation

```
┌─────────────────────────────────────────────────────────┐
│  Tailscale VPN                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Docker Network (private-assistant-internal)     │    │
│  │                                                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │    │
│  │  │ Postgres │ │  Redis   │ │ Brain    │        │    │
│  │  │  (DB)    │ │ (Cache)  │ │ (LLM)    │        │    │
│  │  └──────────┘ └──────────┘ └──────────┘        │    │
│  │                                                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │    │
│  │  │ Mouth    │ │ Heart    │ │ OpenCode │        │    │
│  │  │(WhatsApp)│ │(Schedule)│ │ (Serve)  │        │    │
│  │  └──────────┘ └──────────┘ └──────────┘        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Tailscale Exit Node ──► Internet (anonymized)         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Security Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| VPN | Tailscale | Zero-config mesh networking |
| DNS | DNSCrypt-proxy | Encrypted DNS resolution |
| Proxy | shadowsocks | Encrypted traffic tunneling |
| Anonymization | Tor (optional) | Multi-hop anonymity |
| Firewall | Cripple-NetStrip | Domain blocking, DNS sinkhole |
| Secrets | age encryption | PII and API key protection |

### 5.3 Access Control

| Role | Permissions |
|------|------------|
| godadmin | Full access, killswitch, secret vaults, config changes |
| admin | User management, operational commands |
| user | Personal assistant interactions, own data only |

---

## 6. Bootstrap System

### 6.1 One-Command Install

```bash
curl -fsSL https://get.private-assistant.neohiro.io/install.sh | bash
```

### 6.2 Bootstrap Steps

1. **Pre-flight check**
   - Detect OS (Linux, macOS, Windows WSL)
   - Check prerequisites (Docker, git, curl)
   - Verify disk space (>10GB)

2. **Network setup**
   - Install Tailscale (or connect to existing tailnet)
   - Configure exit node (optional)
   - Set up DNSCrypt-proxy
   - Configure shadowsocks (if enabled)

3. **Disk creation**
   - Create LVM/btrfs volumes for:
     - `/data/postgres` — PostgreSQL data
     - `/data/redis` — Redis cache
     - `/data/backups` — backup storage

4. **Container orchestration**
   - Pull Docker images
   - Start isolated containers:
     - `postgres` — user/session/entity data
     - `redis` — hot cache, rate limiting
     - `brain` — LLM inference
     - `mouth` — WhatsApp (Baileys)
     - `heart` — scheduler
     - `opencode` — coding agent
     - `doctor` — health monitoring

5. **Configuration**
   - Generate secrets (LLM API keys, JWT tokens)
   - Initialize database schemas
   - Register with Heart cadence engine

6. **Verification**
   - Run health checks on all containers
   - Verify WhatsApp QR code pairing
   - Test LLM connectivity

---

## 7. LLM Router

### 7.1 Model Priority Chain

```yaml
llm:
  models:
    - provider: openai
      model: gpt-4o
      priority: 1
      max_tokens: 128000
    - provider: anthropic
      model: claude-sonnet-4-20250514
      priority: 2
      max_tokens: 200000
    - provider: ollama
      model: llama3.3-70b
      priority: 3
      max_tokens: 128000
      endpoint: http://localhost:11434
    - provider: openrouter
      model: google/gemini-2.0-flash-thinking-exp
      priority: 4
      max_tokens: 1000000
```

### 7.2 Fallback Logic

1. Check primary model availability
2. On 429 (rate limit) → try next in chain
3. On 500 (server error) → retry 3x with exponential backoff
4. On quota exceeded → rotate to backup provider
5. On network failure → use cached response or decline gracefully

---

## 8. Development Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Status | Notes |
|------|--------|-------|
| Create neohiro/private-assistant repo | TODO | Core hub |
| Design directory structure | TODO | Based on this plan |
| Set up Docker Compose dev environment | TODO | All services |
| Implement bootstrap/install.sh | TODO | One-command install |
| Configure PostgreSQL schema | TODO | Users, sessions, entities |
| Configure Redis cache | TODO | Hot cache layer |
| Set up Tailscale integration | TODO | Networking |

### Phase 2: Intelligence (Week 3-4)

| Task | Status | Notes |
|------|--------|-------|
| Migrate Brain from neohiro/Brain | TODO | Intelligence hub |
| Migrate Heart from neohiro/Heart | TODO | Cadence engine |
| Wire heartbeat → brain pipeline | TODO | Core loop |
| Implement LLM router | TODO | Multi-provider fallback |
| Implement context manager | TODO | Conversation state |
| Implement tool orchestrator | TODO | Tool calling |

### Phase 3: Communication (Week 5-6)

| Task | Status | Notes |
|------|--------|-------|
| Migrate Mouth from neohiro/Mouth | TODO | Output layer |
| Implement WhatsApp (Baileys) | TODO | Primary channel |
| Implement email delivery | TODO | SMTP integration |
| Implement social media posting | TODO | Twitter, Mastodon, Bluesky |
| Migrate voicemail from neohiro/voicemail | TODO | Intake system |

### Phase 4: Autonomy (Week 7-8)

| Task | Status | Notes |
|------|--------|-------|
| Migrate Mind from neohiro/Mind | TODO | Self-reflection |
| Migrate doctor from neohiro/doctor | TODO | Self-healing |
| Implement self-improvement loop | TODO | Mind → Brain feedback |
| Implement health monitoring | TODO | doctor integration |
| Implement auto-restart on failure | TODO | Self-healing |

### Phase 5: Ecosystem (Week 9-10)

| Task | Status | Notes |
|------|--------|-------|
| Migrate news from neohiro/news | TODO | RSS/HN feeds |
| Migrate network from neohiro/network | TODO | Telemetry backbone |
| Migrate links from neohiro/links | TODO | Platform index |
| Migrate worldmap from neohiro/worldmap | TODO | Data layers |
| Migrate monetization from neohiro/monetization | TODO | Revenue tracking |

### Phase 6: Polish (Week 11-12)

| Task | Status | Notes |
|------|--------|-------|
| Security audit | TODO | Penetration testing |
| Performance optimization | TODO | Redis tuning, caching |
| Documentation | TODO | All modules |
| User testing | TODO | Admin + user flows |
| Kill switch integration | TODO | Emergency stop |

---

## 9. Verification & Testing

### 9.1 Test Categories

| Category | Scope | Tools |
|----------|-------|-------|
| Unit | Individual functions | pytest |
| Integration | Module ↔ Module | pytest + mocks |
| E2E | Full user flows | Playwright, curl |
| Security | Auth, encryption | Semgrep, Bandit |
| Performance | Latency, throughput | k6, locust |

### 9.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .
      - run: mypy src/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/ --cov=src/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: semgrep --config=auto .
      - run: pip install bandit && bandit -r src/
```

---

## 10. Repository Consolidation Map

### 10.1 Merge INTO private-assistant

| Source Repo | Destination | Reason |
|-------------|-------------|--------|
| neohiro/Brain | Brain/ | Core intelligence |
| neohiro/Heart | Heart/ | Cadence engine |
| neohiro/Mouth | Mouth/ | Output layer |
| neohiro/Mind | Mind/ | Self-reflection |
| neohiro/doctor | doctor/ | Self-healing |
| neohiro/voicemail | voicemail/ | Intake |
| neohiro/news | news/ | RSS/HN feeds |
| neohiro/worldmap | worldmap/ | Data layers |
| neohiro/links | links/ | Platform index |
| neohiro/monetization | monetization/ | Revenue tracking |
| neohiro/bootstrap | bootstrap/ | Installer |
| neohiro/whatsapp-bridge | whatsapp-bridge/ | WhatsApp |

### 10.2 Stay SEPARATE

| Repo | Reason |
|------|--------|
| neohiro/userdata | Encrypted PII — must remain isolated |
| neohiro/killswitch | Cross-cutting emergency stop |
| neohiro/links-secret | Secrets vault |
| neohiro/network | Cross-org infrastructure |
| neohiro/opencode-config | OpenCode agent config |

### 10.3 Archive After Migration

| Repo | Status |
|------|--------|
| neohiro/wingman-hub | DEPRECATED — replace with private-assistant |

---

## 11. Critical Path Dependencies

| Order | Task | Blocks |
|-------|------|--------|
| 1 | Create neohiro/private-assistant | All |
| 2 | Set up Docker Compose | Local dev |
| 3 | Implement bootstrap/install.sh | Node setup |
| 4 | Wire Heart → Brain | Core loop |
| 5 | Wire Brain → Mouth | Output |
| 6 | Wire voicemail → Brain | Input |
| 7 | Wire doctor → all | Self-healing |
| 8 | Wire Mind → Brain | Self-reflection |

---

## 12. Open Issues (from REPO_AUDIT_2026-09-02)

### Critical

- [ ] `scan_open_items.py` silent dedupe history loss on corrupt `known_items.json`
- [ ] `data/outbox/` creates outbound alerts as "open items" (queue flood)
- [ ] `data/processed_*` content committed to public repo (PII leakage)
- [ ] All PII in git history — needs scrubbing before migration

### High

- [ ] `git pull --rebase -X theirs` silently discards local commits on conflict
- [ ] `scan_open_items.py` writes `known_items.json` AFTER `items.json` (race condition)
- [ ] `body` field has no length cap (repo bloat + PII amplification)
- [ ] `breach_monitor.py` sends plaintext email addresses in alerts

### Medium

- [ ] Action versions unpinned (supply-chain risk)
- [ ] `pip install` without hash verification
- [ ] 18 includes identical between OSI and FPM (should be shared repo)
- [ ] `scan_open_items.py` collision in 48-bit fingerprint space

---

## 13. Success Metrics

| Metric | Target |
|--------|--------|
| Uptime | >99.5% |
| Response latency (P95) | <2s |
| Self-heal success rate | >95% |
| Heartbeat delivery | 100% |
| Zero PII in public repos | 100% |
| Test coverage | >80% |

---

## 14. References

- [REPO_AUDIT_2026-09-02.md](./REPO_AUDIT_2026-09-02.md) — Detailed audit and migration plan
- [neohiro/Brain](https://github.com/neohiro/Brain) — Intelligence hub (archived)
- [neohiro/Heart](https://github.com/neohiro/Heart) — Cadence engine (archived)
- [neohiro/Mouth](https://github.com/neohiro/Mouth) — Output layer
- [neohiro/news](https://github.com/neohiro/news) — News aggregator (archived)
- [neohiro/network](https://github.com/neohiro/network) — Telemetry backbone
- [neohiro/bootstrap](https://github.com/neohiro/bootstrap) — Installer
- [neohiro/userdata](https://github.com/neohiro/userdata) — Encrypted PII store

---

*Last updated: 2026-09-04*
