# Finalization Mode — auto-resume.js Patch Guide

This document describes the exact changes needed to add finalization mode to
`auto-resume.js` (v1.14.0). Apply the changes in order. Each section lists
the OLD code (to find) and NEW code (to replace).

---

## 0. Version bump

**Find:**
```js
const AUTO_RESUME_VERSION = "1.13.17"
```

**Replace with:**
```js
const AUTO_RESUME_VERSION = "1.14.0"
```

---

## 1. Add finalize-mode constants

**Find:** (after `const tierScore` function, ~line 396)
```js
const tierScore = (modelID) => {
```

**Insert BEFORE:**
```js
// ── finalization-mode constants ───────────────────────────────────────────

const FINALIZE_VERSION = "1.14.0"

/** Finalization-intent phrases — user wants to end/terminate/finalize/finish. */
const DEFAULT_FINALIZE_PHRASES = [
  "end the session", "end this session", "end the task", "end this",
  "terminate the session", "terminate this", "kill the session",
  "finalize", "finalise", "finalization", "finalisation",
  "finish up", "finish this", "finish it", "finish off", "finishing up",
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

const FINALIZE_RE = new RegExp(
  "\\b(?:" + DEFAULT_FINALIZE_PHRASES
    .map(p => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|") + ")\\b",
  "i",
)

/** Handsfree "yes / go ahead" patterns — auto-fire proceedOnAsk without
 *  triggering finalization mode. Short replies only (<=200 chars). */
const HANDSFREE_YES_RE_LIST = [
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

/** Extended question detector for handsfree autopilot.
 *  The key case: "Want me to also update X?" after the model proposed work. */
const HANDSFREE_QUESTION_RE_LIST = [
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
  /\b(also|too|as well)\s+(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
]

/** Finalization phase IDs. */
const FZ = { INACTIVE: 0, ACK: 1, VERIFY: 2, PERSIST: 3, SIGNOFF: 4 }

/** Glyphs for the 4 finalization phases. Distinct shapes, not just colors.
 *  🔎 = scoping, 🛡️ = verifying, 📦 = persisting, 🏁 = signing off. */
const FINALIZE_STATUS_STYLE = {
  [FZ.ACK]:    { glyph: "🔎", label: "finalizing · scoping" },
  [FZ.VERIFY]: { glyph: "🛡️", label: "finalizing · verifying" },
  [FZ.PERSIST]:{ glyph: "📦", label: "finalizing · persisting" },
  [FZ.SIGNOFF]:{ glyph: "🏁", label: "finalizing · sign-off" },
}

/** Detection helpers. */
const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t || t.length > 400) return false
  return FINALIZE_RE.test(t)
}

const looksLikeHandsfreeYes = (text) => {
  const t = String(text ?? "").trim().toLowerCase()
  if (!t || t.length > 200) return false
  return HANDSFREE_YES_RE_LIST.some(re => re.test(t))
}

const isHandsfreeQuestion = (text) => {
  const t = String(text ?? "").trim()
  if (!t || t.length > 500) return false
  return HANDSFREE_QUESTION_RE_LIST.some(re => re.test(t))
}
```

---

## 2. Add finalization prompts

**Find:** (inside the `PROMPTS` object, after `propose: () => ...`)
```js
}
```

**Replace with:**
```js
},

  // ── FINALIZATION MODE PROMPTS ────────────────────────────────────────
  // Four phases take the session off "keep driving toward completion" and
  // onto "complete safely with a working artifact". Each phase is finite,
  // bounded, and verifiable. No phase asks the model to keep going.
  // The plugin goes silent after SIGNOFF (finalizeModeActive stays true so
  // a fresh user prompt re-arms cleanly, but no autopilot fires).

  finalizeAck: () =>
    `${RESUME_TAG} Finalization mode engaged (phase 1/4). The user wants to end this session safely with a functional, updated project — NOT another improvement cycle or drive toward completion.` +
    ` Pause the autopilot. Optimize for a clean artifact the next person can pick up cold.` +
    ` Do now: (a) one-paragraph state of work (what completed, in flight, untouched). (b) Risk flags ONLY (uncommitted changes, failing tests, broken builds, leaked secrets, half-done migrations). (c) The one thing most likely to bite the user after they walk away (one line).` +
    ` Do NOT summarize history. Do NOT start new work. Do NOT propose features. Do NOT ask a question — they asked to finish, so finish. Stay tight: this is a status check, not a deliverable.`,

  finalizeVerify: () =>
    `${RESUME_TAG} Finalization mode (phase 2/4) — verification gate. Run the real toolchain end-to-end and report actual results, not intentions.` +
    ` Minimum checks: build (or compile), test suite, linter, type checker (if applicable), the one smoke command a fresh clone would use. For each: command, exit code, time, pass/fail count.` +
    ` If anything is red: smallest targeted fix (one root cause, not a rewrite), re-run that check only. Do not refactor adjacent code. Do not add features. Do not delete tests to make them pass.` +
    ` If a check cannot run (missing tool, sandbox, blocked registry): say so explicitly with the reason. Stop when everything is green OR when you have a one-line list of what is provably red with exact command and error.` +
    ` No commentary. No recap. Output = command results.`,

  finalizePersist: () =>
    `${RESUME_TAG} Finalization mode (phase 3/4) — persistence pass. Make the work durable across machine restarts and team handoffs.` +
    ` In order: (1) Commit uncommitted work in sensible units (one logical change per commit, match repo message style from last 2 commits). If repo forbids auto-commits, print the exact git commands the user should run. (2) Update drifted docs to match actual final state (README, CHANGELOG, API reference, config table, env-var table). (3) Sweep stale TODO/FIXME/HACK/XXX in files you touched. Resolve or convert to tracked issues (file + line + summary). Never silently delete a TODO. (4) Regenerate time-sensitive artifacts you touched: lockfiles, generated types, snapshots, golden files. (5) Audit logs/stdout for leaked secrets/tokens/hostnames. If found, redact in place and add the scrubber rule that should have caught it.` +
    ` No new features. No 'while we're here' cleanups outside files you touched. If a step doesn't apply, say so in one line and move on.`,

  finalizeSignoff: () =>
    `${RESUME_TAG} Finalization mode (phase 4/4) — sign-off. Output ONE concise message with EXACTLY these four sections in order:` +
    ` DONE: <bullet list of what is in the repo now that wasn't before this session>` +
    ` VERIFIED: <bullet list of commands you actually ran with pass/fail counts — never 'should be green'>` +
    ` FOR YOU: <bullet list of manual steps the user must still do — PR creation, secret rotation, deploy button, anything not safe for an unattended agent>` +
    ` CAVEATS: <bullet list of risks a reviewer should know — unverified assumptions, skipped checks with reasons, known follow-ups>` +
    ` Keep each bullet to one line. No preamble. No recap. No apology.`,

  finalizeReengage: () =>
    `${RESUME_TAG} Finalization overlay released — the user sent a fresh prompt. Session back in normal drive mode. Continue the new request as a senior engineer would: production-grade, verified, no TODO/FIXME, no recap.`,

  handsfreeYes: () =>
    `${RESUME_TAG} Handsfree autopilot: user replied yes/go/handsfree. Continue autonomously with everything you just proposed or listed. No follow-up questions, no recap. Implement end-to-end at senior level: full impl + tests + error handling + doc touches, verified against the real toolchain (build/test/lint/typecheck). When every named follow-up is green, emit the same DONE / VERIFIED / FOR YOU / CAVEATS block. Aim above expectations.` +
    AUTONOMY_DIRECTIVE,
}
```

---

## 3. Add finalization config defaults

**Find:**
```js
  budgetMs: 28_800_000,
```

**Replace with:**
```js
  budgetMs: 28_800_000,
  finalizeMode: true,
  finalizeMaxPhases: 4,
```

---

## 4. Add finalization config loading

**Find:**
```js
    budgetMs: num("OPENCODE_AUTOPILOT_BUDGET_MS", DEFAULTS.budgetMs),
  }
}
```

**Replace with:**
```js
    budgetMs: num("OPENCODE_AUTOPILOT_BUDGET_MS", DEFAULTS.budgetMs),
    finalizeMode: bool("OPENCODE_AUTOPILOT_FINALIZE", DEFAULTS.finalizeMode),
    finalizeMaxPhases: Math.max(1, num("OPENCODE_AUTOPILOT_FINALIZE_MAX_PHASES", DEFAULTS.finalizeMaxPhases)),
  }
}
```

---

## 5. Add finalization glyph to GLYPH_LEAD_RE

**Find:**
```js
  const GLYPH_LEAD_RE = /^\s*(?:🟢|🔁|⏸️|🚫|⏳|💸|🔕|🪙|📋|🧪|✅|🏁|🔄|⏱|💤|🟡|🔴)\s+/u
```

**Replace with:**
```js
  const GLYPH_LEAD_RE = /^\s*(?:🟢|🔁|⏸️|🚫|⏳|💸|🔕|🪙|📋|🧪|✅|🏁|🔄|⏱|💤|🟡|🔴|🔎|🛡️|📦)\s+/u
```

---

## 6. Add finalizeModeActive to session state

**Find:**
```js
        lowBudgetStreak: 0, lowBudgetSig: null, lowBudgetLastFired: false,
      }
```

**Replace with:**
```js
        lowBudgetStreak: 0, lowBudgetSig: null, lowBudgetLastFired: false,
        finalizeModeActive: false, finalizePhase: 0,
      }
```

Also add `finalizeModeActive: false` and `finalizePhase: 0` to the `Object.assign` inside `resetTaskScope` (near `improveActive: false`).

---

## 7. Add finalizePhase to statusKeyOf

**Find:**
```js
    if (s?.proposalSent) return "proposing"
```

**Insert BEFORE:**
```js
    // Finalization mode: distinct glyph per phase.
    if (s?.finalizePhase > 0) {
      const style = FINALIZE_STATUS_STYLE[s.finalizePhase]
      if (style) return `finalize${s.finalizePhase}`
    }
```

**Find:** (in `STATUS_STYLE` object, after `idle:`)
```js
    idle:         { glyph: "💤", label: "armed · idle" },
    fatal:        { glyph: "🔴", label: "armed · unrecoverable" },
  }
```

**Replace with:**
```js
    idle:         { glyph: "💤", label: "armed · idle" },
    fatal:        { glyph: "🔴", label: "armed · unrecoverable" },
    finalize1:    { glyph: "🔎", label: "finalizing · scoping" },
    finalize2:    { glyph: "🛡️", label: "finalizing · verifying" },
    finalize3:    { glyph: "📦", label: "finalizing · persisting" },
    finalize4:    { glyph: "🏁", label: "finalizing · sign-off" },
  }
```

---

## 8. Wire finalization detection into user message handler

**Find:**
```js
              // In-chat switch: exactly "auto-resume off" / "auto-resume on"
              // (leading "/" allowed). Short exact match so prose never trips it.
              const toggleCmd = /^\/?auto[- ]?resume[ :]?(off|on|pause)[.!]?\s*$/i.exec(userText.trim())
```

**Replace with:**
```js
              // In-chat switch: exactly "auto-resume off" / "auto-resume on"
              // (leading "/" allowed). Short exact match so prose never trips it.
              const toggleCmd = /^\/?auto[- ]?resume[ :]?(off|on|pause)[.!]?\s*$/i.exec(userText.trim())
              if (toggleCmd) {
                handleToggleCommand(info.sessionID, toggleCmd[1].toLowerCase())
                break
              }
              // Finalization intent: user says "end / terminate / finalize / finish / done".
              // Enter finalization mode: clear improve/drive state, enter phase 1.
              if (cfg.autonomy && cfg.finalizeMode && !ours && !isOptedOut(info.sessionID)) {
                if (looksLikeFinalization(userText)) {
                  const s0 = state(info.sessionID)
                  // Clear all active states so finalization starts clean.
                  s0.improveActive = false
                  s0.improveDone = cfg.improveCycles  // suppress further improve passes
                  s0.proposalSent = true
                  s0.finalizeModeActive = true
                  s0.finalizePhase = FZ.ACK
                  s0.nudges += 1
                  log("info", "finalization intent detected — phase 1", { sessionID: info.sessionID })
                  notice(`${RESUME_TAG}: Finalization mode — 🔎 scoping. Working toward a clean sign-off.`, "info")
                  schedule(info.sessionID, cfg.nudgeDelayMs, {
                    kind: "finalizeAck",
                    prompt: PROMPTS.finalizeAck,
                  })
                  break
                }
              }
```

---

## 9. Wire finalization into evaluateIdle

**Find:**
```js
      // Implicit todo lists: markdown checkboxes in the assistant's own reply
      // count as a todo list even when the todo tool was never used.
      const replyText = (lastAssistant.parts ?? [])
```

**Insert BEFORE (inside `evaluateIdle`, as the FIRST check after `if (!errored && hasContent)`):**
```js
      // Finalization mode: drive through the 4 phases.
      if (s.finalizeModeActive && s.finalizePhase > 0) {
        if (s.finalizePhase >= FZ.SIGNOFF) {
          // Phase 4 complete — go silent but keep finalizeModeActive so
          // a fresh user prompt can re-arm via finalizeReengage.
          log("info", "finalization complete", { sessionID })
          notice(`${RESUME_TAG}: Finalization complete. 🏁`, "success")
          // Don't reset finalizeModeActive here — a new user prompt triggers
          // finalizeReengage which clears it cleanly.
          return
        }
        const nextPhase = Math.min(s.finalizePhase + 1, cfg.finalizeMaxPhases)
        const prompts = {
          [FZ.ACK]:    PROMPTS.finalizeAck,
          [FZ.VERIFY]: PROMPTS.finalizeVerify,
          [FZ.PERSIST]:PROMPTS.finalizePersist,
          [FZ.SIGNOFF]:PROMPTS.finalizeSignoff,
        }
        const prompt = prompts[nextPhase] ?? PROMPTS.finalizeAck
        const glyph = FINALIZE_STATUS_STYLE[nextPhase]?.glyph ?? "🏁"
        s.finalizePhase = nextPhase
        s.nudges += 1
        log("info", `finalization phase ${nextPhase}/4`, { sessionID })
        queueTitleRefresh(sessionID)
        schedule(sessionID, cfg.nudgeDelayMs, { kind: `finalize${nextPhase}`, prompt })
        return
      }

```

---

## 10. Wire finalizeReengage into user message handler

**Find:**
```js
              s0.lastTurnHadText = false // new turn begins
              break
            }
```

**Insert AFTER that block (still inside `if (info.role === "user")`, after the existing reset/follow-up logic):**
```js
              // If finalize mode is active and user sent a real prompt, re-engage.
              // This fires BEFORE any follow-up detection so finalization cleanly
              // exits when the user starts new work.
              if (s0.finalizeModeActive && s0.finalizePhase > 0 && !ours) {
                log("info", "finalization re-engage — user sent new prompt", { sessionID: info.sessionID })
                s0.finalizeModeActive = false
                s0.finalizePhase = 0
                schedule(info.sessionID, cfg.nudgeDelayMs, {
                  kind: "finalizeReengage",
                  prompt: PROMPTS.finalizeReengage,
                })
                break
              }
```

---

## 11. Enhance proceedOnAsk detection (handsfree question + yes)

**Find:**
```js
          if (text && text.trim()) {
            const asked = QUESTION_PATTERNS.some((re) => re.test(text))
            const stubbed = looksLikeContinuationStub(text) || looksLikeContinuationLong(text)
            if (asked || stubbed) {
```

**Replace with:**
```js
          if (text && text.trim()) {
            // Handsfree question: "Want me to also update X?" after the model
            // proposed follow-up work. Treat as auto-proceed (NOT finalization).
            const handsfreeQ = isHandsfreeQuestion(text)
            const asked = QUESTION_PATTERNS.some((re) => re.test(text)) || handsfreeQ
            const stubbed = looksLikeContinuationStub(text) || looksLikeContinuationLong(text)
            if (asked || stubbed) {
              // Check if user already replied "yes / go / handsfree" to the model's
              // proposal. If so, fire handsfreeYes (continues work, does NOT finalize).
              // This handles the case where the model asked a question AND the user
              // already replied "yes" before the plugin evaluated the turn.
              if (handsfreeQ) {
                // Model asked a handsfree question (e.g. "Want me to also update X?").
                // The model's reply already delivered the answer; we just need to
                // tell it to continue. Fire proceedOnAsk but label it handsfree.
                s.proceedCount += 1
                s.nudges += 1
                log("info", "handsfree question — auto-proceeding", { sessionID })
                schedule(sessionID, cfg.nudgeDelayMs, {
                  kind: "handsfreeYes",
                  prompt: PROMPTS.handsfreeYes,
                })
                return
              }
```

---

## 12. Add finalizeReengage to `lastInjectKind` block

**Find:**
```js
      // Reset follow-up counters on the inject side so a new task boundary
      // (or a finalize-reengage) re-arms the subsystem cleanly.
      if (kind === "improve" || kind === "propose" || kind === "todos" ||
          kind === "debug" || kind === "proceed" || kind === "keepGoing") {
        s.lastInjectKind = kind
      }
```

**Replace with:**
```js
      // Reset follow-up counters on the inject side so a new task boundary
      // (or a finalize-reengage) re-arms the subsystem cleanly.
      if (kind === "improve" || kind === "propose" || kind === "todos" ||
          kind === "debug" || kind === "proceed" || kind === "keepGoing" ||
          kind.startsWith("finalize")) {
        s.lastInjectKind = kind
      }
```

---

## 13. Bump the header docstring

Add to the SUBSYSTEM 4 block in the header:
```
 *   • FINALIZATION MODE: when the user says "end", "terminate", "finalize",
 *     "finish up", "wrap it up", "that's all", "done", "we're done", or
 *     similar — the plugin detects the intent, drives through 4 phases
 *     (scope → verify → persist → sign-off), and leaves a clean, working
 *     artifact. Distinct glyphs (🔎🛡️📦🏁) show the current phase.
```

Add to the CONFIGURATION section:
```
 *  OPENCODE_AUTOPILOT_FINALIZE         enable finalization mode        (true)
 *  OPENCODE_AUTOPILOT_FINALIZE_MAX_PHASES max finalization phases     (4)
```

---

## Testing

Run the tests after applying:
```bash
node tests/finalize.test.mjs
node tests/smoke.mjs
```

Expected: all F1–F4 finalize tests pass + all smoke tests pass.
