# Finalization Mode — PATCH.md

This document describes the changes required to add finalization mode to
`auto-resume.js` (v1.13.17 → v1.14.0).

Apply the changes in order. Each section lists: **what**, **where** (line
number or search string), and **old → new**.

---

## 0. Version bump

**Search:** `const AUTO_RESUME_VERSION = "1.13.17"`
**Replace with:** `const AUTO_RESUME_VERSION = "1.14.0"`

---

## 1. New DEFAULTS entries (after `budgetMs`)

**Search:** `budgetMs: 28_800_000,\n}`
**Replace with:**
```javascript
  budgetMs: 28_800_000,
  finalizeMode: true,
  finalizeMaxPhases: 4,
  finalizeVerify: true,
  finalizePhrases: "",
}
```

---

## 2. New loadConfig() entries (after `budgetMs`)

**Search:**
```javascript
    budgetMs: num("OPENCODE_AUTOPILOT_BUDGET_MS", DEFAULTS.budgetMs),
  }
```

**Replace with:**
```javascript
    budgetMs: num("OPENCODE_AUTOPILOT_BUDGET_MS", DEFAULTS.budgetMs),
    finalizeMode: bool("OPENCODE_AUTOPILOT_FINALIZE", DEFAULTS.finalizeMode),
    finalizeMaxPhases: Math.max(1, num("OPENCODE_AUTOPILOT_FINALIZE_MAX_PHASES", DEFAULTS.finalizeMaxPhases)),
    finalizeVerify: bool("OPENCODE_AUTOPILOT_FINALIZE_VERIFY", DEFAULTS.finalizeVerify),
    finalizePhrases: str("OPENCODE_AUTOPILOT_FINALIZE_PHRASES", DEFAULTS.finalizePhrases),
  }
```

---

## 3. New PROMPTS entries (after `propose:`)

**Search:**
```javascript
  propose: () =>
    `${RESUME_TAG} Todos complete, flawless execution. Do NOT implement more. Don't summarize the work. Wrap-up = NEW info only:` +
    ` (1) Verification status — what you ran (build/test/lint/typecheck) and results; flag anything unverified.` +
    ` (2) Known limitations, risks, assumptions a reviewer should know.` +
    ` (3) Up to 3 follow-up improvement proposals, each with expected payoff — aim above user expectations.`,
}
```

**Replace with:**
```javascript
  propose: () =>
    `${RESUME_TAG} Todos complete, flawless execution. Do NOT implement more. Don't summarize the work. Wrap-up = NEW info only:` +
    ` (1) Verification status — what you ran (build/test/lint/typecheck) and results; flag anything unverified.` +
    ` (2) Known limitations, risks, assumptions a reviewer should know.` +
    ` (3) Up to 3 follow-up improvement proposals, each with expected payoff — aim above user expectations.`,
  finalizeAck: () =>
    `${RESUME_TAG} Finalization mode engaged (phase 1/4). The user signaled they want to end this session and its work safely with a functional, updated project — NOT another improvement cycle or drive toward completion.` +
    ` Pause the autopilot. From here on, optimize for a clean, working artifact the next person (or the user on Monday) can pick up cold.` +
    ` Do now, briefly: (a) One-paragraph state of the work: what was just completed, what is in flight, what is untouched.` +
    ` (b) Risk flags ONLY: uncommitted changes, failing/missing tests, broken builds, leaked secrets, half-done migrations, anything a reviewer would push back on.` +
    ` (c) The single most likely thing to bite the user after they walk away (one line, plain English).` +
    ` Do NOT summarize history. Do NOT start new work. Do NOT propose features. Do NOT ask the user a question — they asked to finish, so finish.` +
    ` Stay tight: this reply is a status check, not a deliverable. Senior-grade output: verify before claiming done. No TODOs, no apology, no recap.`,
  finalizeVerify: () =>
    `${RESUME_TAG} Finalization mode (phase 2/4) — verification gate. Before signing off, run the real toolchain end-to-end and report actual results, not intentions.` +
    ` Minimum checks: build (or compile), test suite, linter, type checker (if applicable), the one smoke command a fresh clone would use.` +
    ` For each: command run, exit code, time taken, pass/fail count. If anything is red, apply the smallest targeted fix (one root cause, not a rewrite) and re-run only that check. Do not refactor adjacent code. Do not add features. Do not delete tests to make them pass.` +
    ` If a check cannot run (missing tool, sandbox), say so explicitly with the reason — never claim 'green' by skipping. Stop when everything you ran is green, OR when you have a one-line list of what is provably red with the exact command and error.` +
    ` No commentary. No recap. Output = the command results. Senior-grade: verify before claiming done. No TODOs, no apology.`,
  finalizePersist: () =>
    `${RESUME_TAG} Finalization mode (phase 3/4) — persistence pass. Make the work durable so the next session can resume cleanly.` +
    ` In order: (1) Commit uncommitted work in sensible units (read 2 prior commits to match style; skip if repo forbids auto-commits, print exact git commands instead).` +
    ` (2) Update docs that drifted from code: README, CHANGELOG, API reference, config table, env-var table (use actual final state — no aspirational text).` +
    ` (3) Sweep for stale TODO/FIXME/HACK/XXX in files you touched this session. Resolve or convert to tracked issues (file + line + one-line summary). Never silently delete a TODO that signals a real follow-up.` +
    ` (4) Regenerate time-sensitive artifacts: lockfiles, generated types, snapshots, golden files, schema dumps, index files.` +
    ` (5) Audit logs for leaked secrets/tokens/internal hostnames before they ship. If found, redact in place and add the exact scrubber rule.` +
    ` No new features. No drive-by cleanups outside files you touched. No refactors. If a step doesn't apply, say so in one line. Senior-grade: verify before claiming done. No TODOs, no apology.`,
  finalizeSignoff: () =>
    `${RESUME_TAG} Finalization mode (phase 4/4) — sign-off. Output ONE concise message with EXACTLY these four sections:` +
    ` DONE: <bullet list of what is in the repo right now that wasn't before this session>` +
    ` VERIFIED: <bullet list of commands you actually ran, with their pass/fail counts — never 'should be green'>` +
    ` FOR YOU: <bullet list of manual steps the user must still do — PR creation, secret rotation, deploy button, anything not safe for an unattended agent>` +
    ` CAVEATS: <bullet list of risks a reviewer should know — unverified assumptions, skipped checks with reasons, known follow-ups>` +
    ` Keep each bullet to one line. No preamble. No recap. No apology.`,
  finalizeReengage: () =>
    `${RESUME_TAG} Finalization overlay released — the user sent a fresh prompt. The session is back in normal drive mode. Continue the new request as a senior engineer would: production-grade, verified, no TODO/FIXME, no recap.`,
  handsfreeYes: () =>
    `${RESUME_TAG} Handsfree autopilot: the user replied 'yes / go / handsfree'. Continue autonomously with everything you just proposed or listed — including the WORKSPACE REFS update and any other follow-ups you named.` +
    ` No follow-up questions, no recap. Implement end-to-end at senior level: full impl + tests + error handling + doc touches, verified against the real toolchain (build/test/lint/typecheck).` +
    ` When every named follow-up is green, emit a DONE / VERIFIED / FOR YOU / CAVEATS block. Senior-grade: verify before claiming done. Exceed expectations.`,
}
```

---

## 4. New FINALIZE_PHRASES build (after `looksLikeContinuationLong`)

**Search:**
```javascript
const looksLikeContinuationLong = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  return CONTINUATION_ANYWHERE.some((re) => re.test(t))
}
```

**Replace with:**
```javascript
const looksLikeContinuationLong = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  return CONTINUATION_ANYWHERE.some((re) => re.test(t))
}

// ── finalization mode ─────────────────────────────────────────────────────

const FINALIZE_PHRASE_LIST = (() => {
  const base = [
    "end the session", "end this session", "end the task", "end this",
    "terminate the session", "terminate this", "kill the session",
    "finalize", "finalise", "finalization", "finalisation",
    "finish up", "finish this", "finish it", "finish off",
    "wrap up", "wrap this up", "wrap it up",
    "close out", "close this out", "close it out",
    "that's all", "that is all", "that's it", "that'll do",
    "we're done", "we are done", "we're finished",
    "i'm done", "i am done",
    "done for today", "done for now",
    "ship it", "merge it", "deploy it",
    "call it done", "call it a day", "call it complete",
    "wind down", "wind it down",
    "session over", "that's a wrap",
    "let's stop here", "lets stop here", "stop here",
    "ok that's enough", "okay that's enough",
  ]
  const extra = cfg.finalizePhrases
    ? cfg.finalizePhrases.split(",").map(s => s.trim().toLowerCase()).filter(Boolean)
    : []
  return [...new Set([...base, ...extra])]
})()

const FINALIZE_RE = new RegExp(
  "\\b(?:" + FINALIZE_PHRASE_LIST
    .map(p => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|") + ")\\b",
  "i",
)

const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t || t.length > 400) return false
  return FINALIZE_RE.test(t)
}

const HANDSFREE_YES_RE = [
  /^(yes|yep|yeah|ya|sure|ok|okay|k|kk|alright|go|proceed|do it|go ahead|y)\b[.!]?\s*$/i,
  /^(yes|yep|yeah|sure|ok|okay|alright),\s*(please|do it|go ahead|proceed|continue)\b[.!]?\s*$/i,
  /^(yes|yep|yeah|sure|ok|okay)\s+to\s+(your|the|all|that)\b.*$/i,
  /^continue(\s+and\s+(continue|finish|proceed))?\b[.!]?\s*$/i,
  /^hands\s*-?\s*free\b[.!]?\s*$/i,
  /^auto\s*-?\s*proceed\b[.!]?\s*$/i,
  /^y\s+to\s+all\b[.!]?\s*$/i,
  /^yes\s+to\s+all\b[.!]?\s*$/i,
  /^affirmative\b[.!]?\s*$/i,
  /^go\s+ahead\s+and\s+(do|update|fix|ship|merge|deploy)\b.*$/i,
  /^(yes|yep|yeah|sure),\s+(do|update|fix|ship|merge|deploy)\s+(it|them|all|everything)\b[.!]?\s*$/i,
]
const looksLikeHandsfreeYes = (text) => {
  const t = String(text ?? "").trim().toLowerCase()
  if (!t || t.length > 200) return false
  return HANDSFREE_YES_RE.some(re => re.test(t))
}

const HANDSFREE_QUESTION_RE = [
  /\bshall i\b/i, /\bshould i\b/i, /\bwould you like me\b/i,
  /\bdo you want me to\b/i, /\bwant me to\b/i,
  /\bcan i (proceed|continue|start|begin|go ahead)\b/i,
  /\bshould we\b/i, /\blet me know (if|when|whether)\b/i,
  /\bawait(ing)? (your|further) (confirmation|instructions|approval|input)\b/i,
  /\bwaiting for your\b/i, /\bprompt (me|you) when\b/i,
  /\bwant me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bdo you want me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshould i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bcan i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bwould you like me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshall i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
]
const isHandsfreeQuestion = (text) => {
  const t = String(text ?? "").trim()
  if (!t || t.length > 500) return false
  return HANDSFREE_QUESTION_RE.some(re => re.test(t))
}

// Finalization phase → STATUS_STYLE glyph+label
const FINALIZE_STYLE = {
  1: { glyph: "🔎", label: "finalizing · scoping" },
  2: { glyph: "🛡️", label: "finalizing · verifying" },
  3: { glyph: "📦", label: "finalizing · persisting" },
  4: { glyph: "🏁", label: "finalizing · sign-off" },
}
const finalizeStatus = (phase) => FINALIZE_STYLE[phase] ?? null
```

---

## 5. New session state fields (in `state()` object)

**Search:**
```javascript
        lowBudgetStreak: 0, lowBudgetSig: null, lowBudgetLastFired: false,
      }
```

**Replace with:**
```javascript
        lowBudgetStreak: 0, lowBudgetSig: null, lowBudgetLastFired: false,
        finalizePhase: 0,  // 0 = inactive, 1-4 = active phases
        finalizeStartedAt: 0,
        finalizeHandsfreeAt: 0,
      }
```

---

## 6. New resetTaskScope entries (reset finalize fields)

**Search:**
```javascript
      lowBudgetStreak: 0, lowBudgetSig: null, userPaused: false, emptyStreak: false,
      lastErrorName: null, lastErrorSig: null,
```

**Replace with:**
```javascript
      lowBudgetStreak: 0, lowBudgetSig: null, userPaused: false, emptyStreak: false,
      lastErrorName: null, lastErrorSig: null,
      finalizePhase: 0, finalizeStartedAt: 0, finalizeHandsfreeAt: 0,
```

---

## 7. GLYPH_LEAD_RE update (add 🔎🛡️📦🏁)

**Search:**
```javascript
  const GLYPH_LEAD_RE = /^\s*(?:🟢|🔁|⏸️|🚫|⏳|💸|🔕|🪙|📋|🧪|✅|🏁|🔄|⏱|💤|🟡|🔴)\s+/u
```

**Replace with:**
```javascript
  const GLYPH_LEAD_RE = /^\s*(?:🟢|🔁|⏸️|🚫|⏳|💸|🔕|🪙|📋|🧪|✅|🏁|🔄|⏱|💤|🟡|🔴|🔎|🛡️|📦)\s+/u
```

---

## 8. STATUS_STYLE update (add finalize phase entries)

**Search:**
```javascript
    fatal:        { glyph: "🔴", label: "armed · unrecoverable" },
  }
```

**Replace with:**
```javascript
    fatal:        { glyph: "🔴", label: "armed · unrecoverable" },
    finalize1:    { glyph: "🔎", label: "finalizing · scoping" },
    finalize2:    { glyph: "🛡️", label: "finalizing · verifying" },
    finalize3:    { glyph: "📦", label: "finalizing · persisting" },
    finalize4:    { glyph: "🏁", label: "finalizing · sign-off" },
  }
```

---

## 9. statusKeyOf update (add finalize sub-state priority)

**Search:**
```javascript
    // Armed sub-states: most actionable signal first.
    // Fatal / auth error: 🔴 tells user it can't self-heal.
    if (s?.lastErrorName === "fatal" || s?.lastErrorName === "auth") return "fatal"
    if (s?.lowBudgetStreak > 0) return "lowBudget"
```

**Replace with:**
```javascript
    // Armed sub-states: most actionable signal first.
    // Finalization phases take priority over all other sub-states so the user
    // always sees the active finalization stage even when todos or improve are
    // also active (the autopilot has shifted from "keep driving" to "finish safely").
    if (s?.finalizePhase > 0) return `finalize${s.finalizePhase}`
    // Fatal / auth error: 🔴 tells user it can't self-heal.
    if (s?.lastErrorName === "fatal" || s?.lastErrorName === "auth") return "fatal"
    if (s?.lowBudgetStreak > 0) return "lowBudget"
```

---

## 10. New evaluateIdle finalization branch (before the todo/autopilot logic)

**Search:**
```javascript
      // The agent ended its turn by asking a question or announcing more
      // work ("Continue to finalize.") instead of finishing — keep it going.
      if (open.length === 0 && s.lastInjectKind !== "propose" && cfg.autonomy && cfg.proceedOnAsk &&
```

**Replace with:**
```javascript
      // ── FINALIZATION MODE ───────────────────────────────────────────
      // User said "end / terminate / finalize / finish up / wrap it up / done
      // / ship it / that's all" or similar finalization signal.  Shift from
      // the "keep driving toward completion" track to the "finish safely" track.
      // Only fires once per finalization trigger; phases 1-4 advance
      // sequentially; the plugin stays silent after phase 4 unless the user
      // sends a new prompt (which re-arms normal autopilot via resetTaskScope).
      if (cfg.autonomy && cfg.finalizeMode && !s.finalizePhase && s.nudges < cfg.maxNudges && budgetLeft(s)) {
        const userText = (lastAssistant.parts ?? [])
          .map((x) => (x?.type === "text" ? x.text : "")).join(" ").trim()
        if (userText && looksLikeFinalization(userText)) {
          s.finalizePhase = 1
          s.finalizeStartedAt = Date.now()
          s.nudges += 1
          log("info", "finalization mode engaged", { sessionID, phase: 1 })
          notice(`${RESUME_TAG}: Finalization mode engaged 🔎 — driving to clean sign-off.`, "info")
          schedule(sessionID, cfg.nudgeDelayMs, {
            kind: "finalizeAck",
            prompt: PROMPTS.finalizeAck,
          })
          return
        }
      }

      // Advance finalization phase if the current phase prompt has delivered.
      // Each phase runs once and advances on the next idle evaluation.
      if (cfg.autonomy && cfg.finalizeMode && s.finalizePhase > 0 && s.finalizePhase < cfg.finalizeMaxPhases) {
        const prevKind = `finalize${["", "Ack", "Verify", "Persist"][s.finalizePhase]}`
        if (s.lastInjectKind === prevKind) {
          s.finalizePhase += 1
          s.nudges += 1
          log("info", "finalization phase advance", { sessionID, phase: s.finalizePhase })
          const promptMap = {
            2: PROMPTS.finalizeVerify,
            3: PROMPTS.finalizePersist,
            4: PROMPTS.finalizeSignoff,
          }
          schedule(sessionID, cfg.nudgeDelayMs, {
            kind: `finalize${["", "Ack", "Verify", "Persist", "Signoff"][s.finalizePhase]}`,
            prompt: promptMap[s.finalizePhase] ?? PROMPTS.finalizeSignoff,
          })
          return
        }
      }

      // ── AUTO-PROCEED (handsfree autopilot) ──────────────────────────
      // The agent ended its turn by asking a question or announcing more
      // work ("Continue to finalize.") instead of finishing — keep it going.
      if (open.length === 0 && s.lastInjectKind !== "propose" && cfg.autonomy && cfg.proceedOnAsk &&
```

---

## 11. New handsfree-yet branch in evaluateIdle (before the finalize branch)

**Add after the finalizePhase > 0 block, BEFORE the question detection block:**

```javascript
      // ── HANDSFREE YES TO PROPOSAL ──────────────────────────────────
      // The user replied "yes", "go ahead", "handsfree", "yes to your proposal",
      // "yes to all, continue handsfree" to the model's proposal block.
      // This should auto-proceed WITHOUT flipping into finalization mode.
      if (cfg.autonomy && cfg.proceedOnAsk && s.lastInjectKind === "propose" &&
          s.proceedCount < cfg.maxProceeds && s.nudges < cfg.maxNudges && budgetLeft(s)) {
        const userText = (lastAssistant.parts ?? [])
          .map((x) => (x?.type === "text" ? x.text : "")).join(" ").trim()
        if (userText && looksLikeHandsfreeYes(userText)) {
          s.proceedCount += 1
          s.nudges += 1
          s.finalizeHandsfreeAt = Date.now()
          log("info", "handsfree yes — auto-proceeding on proposal", { sessionID })
          schedule(sessionID, cfg.nudgeDelayMs, {
            kind: "handsfreeYes",
            prompt: PROMPTS.handsfreeYes,
          })
          return
        }
      }
```

---

## 12. Extended question detection (update `asked` in proceed block)

**Search:**
```javascript
          const asked = QUESTION_PATTERNS.some((re) => re.test(text))
          const stubbed = looksLikeContinuationStub(text) || looksLikeContinuationLong(text)
          if (asked || stubbed) {
            s.proceedCount += 1
            s.nudges += 1
            log("info", asked ? "agent asked a question — proceeding autonomously" : "agent announced continuation but stopped — resuming", { sessionID })
            schedule(sessionID, cfg.nudgeDelayMs, {
              kind: "proceed",
              prompt: asked ? PROMPTS.proceed : PROMPTS.keepGoing,
            })
            return
          }
```

**Replace with:**
```javascript
          const asked = QUESTION_PATTERNS.some((re) => re.test(text)) ||
                        isHandsfreeQuestion(text)
          const stubbed = looksLikeContinuationStub(text) || looksLikeContinuationLong(text)
          if (asked || stubbed) {
            s.proceedCount += 1
            s.nudges += 1
            log("info", asked ? "agent asked a question — proceeding autonomously" : "agent announced continuation but stopped — resuming", { sessionID })
            schedule(sessionID, cfg.nudgeDelayMs, {
              kind: "proceed",
              prompt: asked ? PROMPTS.proceed : PROMPTS.keepGoing,
            })
            return
          }
```

---

## 13. Toggle command update (add "finalize" command)

**Search:**
```javascript
               // In-chat switch: exactly "auto-resume off" / "auto-resume on"
               // (leading "/" allowed). Short exact match so prose never trips it.
               const toggleCmd = /^\/?auto[- ]?resume[ :]?(off|on|pause)[.!]?\s*$/i.exec(userText.trim())
               if (toggleCmd) {
                 handleToggleCommand(info.sessionID, toggleCmd[1].toLowerCase())
                 break
               }
```

**Replace with:**
```javascript
               // In-chat switch: "auto-resume off / on / pause / finalize"
               // (leading "/" allowed). Short exact match so prose never trips it.
               const toggleCmd = /^\/?auto[- ]?resume[ :]?(off|on|pause|finalize)[.!]?\s*$/i.exec(userText.trim())
               if (toggleCmd) {
                 handleToggleCommand(info.sessionID, toggleCmd[1].toLowerCase())
                 break
               }
```

---

## 14. handleToggleCommand update (handle "finalize" mode)

**Search:**
```javascript
    // mode === "on"
    const wasOff = isOptedOut(sessionID)
    if (offStore.map.delete(sessionID)) offStore.save()
    if (pauseStore.map.delete(sessionID)) pauseStore.save()
    if (persistedStops.delete(sessionID)) stopStore.save()
    resetTaskScope(s)
    s.userStopped = false
    s.userPaused = false
```

**Replace with:**
```javascript
    // mode === "finalize" — explicitly engage finalization mode (like saying
    // "end this session" but without waiting for the model to detect it).
    if (mode === "finalize") {
      s.finalizePhase = 1
      s.finalizeStartedAt = Date.now()
      s.userStopped = false
      s.userPaused = false
      if (offStore.map.delete(sessionID)) offStore.save()
      if (pauseStore.map.delete(sessionID)) pauseStore.save()
      if (persistedStops.delete(sessionID)) stopStore.save()
      log("info", "finalization mode explicitly engaged", { sessionID })
      notice(`${RESUME_TAG}: Finalization mode engaged 🔎 — driving to clean sign-off.`, "info")
      queueTitleRefresh(sessionID)
      schedule(sessionID, cfg.nudgeDelayMs, {
        kind: "finalizeAck",
        prompt: PROMPTS.finalizeAck,
      })
      return
    }
    // mode === "on"
    const wasOff = isOptedOut(sessionID)
    if (offStore.map.delete(sessionID)) offStore.save()
    if (pauseStore.map.delete(sessionID)) pauseStore.save()
    if (persistedStops.delete(sessionID)) stopStore.save()
    resetTaskScope(s)
    s.userStopped = false
    s.userPaused = false
```

---

## 15. New config comment entries

**Search:**
```javascript
 *  OPENCODE_AUTOPILOT_MAX_COST_USD       spend cap per task, USD     (10, 0=off)
 */
```

**Replace with:**
```javascript
 *  OPENCODE_AUTOPILOT_MAX_COST_USD       spend cap per task, USD     (10, 0=off)
 *  OPENCODE_AUTOPILOT_FINALIZE           finalization mode           (true)
 *  OPENCODE_AUTOPILOT_FINALIZE_MAX_PHASES max finalization phases  (4)
 *  OPENCODE_AUTOPILOT_FINALIZE_VERIFY   require explicit verify    (true)
 *  OPENCODE_AUTOPILOT_FINALIZE_PHRASES  extra comma-separated
 *                                        finalization keywords       (override)
 */
```

---

## 16. New subsystem 4 doc entry

**Search:**
```javascript
 *   • BEYOND EXPECTATIONS: before wrapping up, runs a self-critique pass —
 *     the model reviews its own work for correctness/perf/security/robustness
 *     improvements and implements the safe ones (capped number of cycles)
```

**Replace with:**
```javascript
 *   • BEYOND EXPECTATIONS: before wrapping up, runs a self-critique pass —
 *     the model reviews its own work for correctness/perf/security/robustness
 *     improvements and implements the safe ones (capped number of cycles)
 *   • FINALIZATION MODE: when the user says "end", "terminate", "finalize",
 *     "finish up", "wrap it up", "that's all", "done", "we're done", or
 *     similar, the plugin detects the intent, shifts from the "keep driving
 *     toward completion" track to a 4-phase "finish safely" track:
 *       🔎 phase 1 — acknowledge + scope: what's done, what's risky
 *       🛡️ phase 2 — verification gate: build/test/lint, fix if red
 *       📦 phase 3 — persistence: commit, docs, TODO sweep, lockfiles
 *       🏁 phase 4 — sign-off: DONE / VERIFIED / FOR YOU / CAVEATS
 *     Distinct glyphs and prompts make the mode unambiguous. The plugin
 *     stays silent after phase 4; a new user prompt re-arms normal mode.
 *     Also fires on "auto-resume finalize" (explicit) or any of the
 *     FINALIZE_PHRASES regex matches in the user's last message.
 *     Handsfree "yes / go / handsfree" replies to proposal blocks are
 *     auto-applied without triggering finalization mode.
```
