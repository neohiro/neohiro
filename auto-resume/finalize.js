/**
 * auto-resume.js — resilience + unattended-autonomy plugin for OpenCode.
 * v1.14.0 — finalization mode (end/terminate/finalize/finish/done detection)
 */
import { writeFile, rename, unlink } from "node:fs/promises"

export const FINALIZE_VERSION = "1.14.0"

// Default finalization phrases — match end/terminate/finalize/finish/done/close.
const DEFAULT_FINALIZE_PHRASES = [
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

const FINALIZE_RE = new RegExp(
  "\\b(?:" + DEFAULT_FINALIZE_PHRASES.map(p =>
    p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  ).join("|") + ")\\b",
  "i",
)

/** Public: returns true when text contains a finalization-intent phrase. */
export const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 400) return false
  return FINALIZE_RE.test(t)
}

/** Returns true when the user prompt is a short "yes / go ahead" reply
 *  that should be auto-applied (handsfree autopilot) instead of blocking. */
export const looksLikeHandsfreeYes = (text) => {
  const t = String(text ?? "").trim().toLowerCase()
  if (!t) return false
  if (t.length > 200) return false
  const handsfreePatterns = [
    /^(yes|yep|yeah|ya|sure|ok|okay|k|kk|alright|go|proceed|do it|go ahead|y)\b[.!]?\s*$/i,
    /^(yes|yep|yeah|sure|ok|okay|alright),\s*(please|do it|go ahead|proceed|continue)\b[.!]?\s*$/i,
    /^(yes|yep|yeah|sure|ok|okay)\s+to\s+(your|the|all|that)\b.*$/i,
    /^continue(\s+and\s+(continue|finish|proceed))?\b[.!]?\s*$/i,
    /^hands\s*-?\s*free\b[.!]?\s*$/i,
    /^auto\s*-?\s*proceed\b[.!]?\s*$/i,
    /^y\s+to\s+all\b[.!]?\s*$/i,
    /^yes\s+to\s+all\b[.!]?\s*$/i,
    /^affirmative\b[.!]?\s*$/i,
  ]
  return handsfreePatterns.some(re => re.test(t))
}

/** Compact version of the finalization prompt — used when the model has
 *  already produced a status block in this session and just needs to know
 *  the mode is still on. ~120 chars vs ~450. */
const FINALIZE_FOOTER =
  " Done = production-grade with verification. No TODOs, no recap. Documented assumptions. Exceed expectations."

const PROMPTS = {
  /** Phase 1 of finalization (1/4): Acknowledge + scope. The model has been
   *  told the user wants to end safely. Output = a tight status block. */
  finalizeAck: () =>
    "[auto-resume] Finalization mode engaged (phase 1/4). The user signaled they want to end this session and its work safely with a functional, updated project — NOT another improvement cycle or drive toward completion." +
    " Pause the autopilot. From here on, optimize for a clean, working artifact the next person (or the user on Monday) can pick up cold." +
    " Do now, briefly:" +
    " (a) One-paragraph state of the work: what was just completed, what is in flight, what is untouched." +
    " (b) Risk flags ONLY: uncommitted changes, failing/missing tests, broken builds, leaked secrets, half-done migrations, anything a reviewer would push back on." +
    " (c) The single most likely thing to bite the user after they walk away (one line, plain English)." +
    " Do NOT summarize history. Do NOT start new work. Do NOT propose features. Do NOT ask the user a question — they asked to finish, so finish." +
    " Stay tight: this reply is a status check, not a deliverable." +
    FINALIZE_FOOTER,

  /** Phase 2 (2/4): Real verification gate — build/test/lint, no skipping. */
  finalizeVerify: () =>
    "[auto-resume] Finalization mode (phase 2/4) — verification gate. Before signing off, run the real toolchain end-to-end and report actual results, not intentions." +
    " Minimum checks for the stack you touched: build (or compile), test suite, linter, type checker (if applicable), the one smoke command a fresh clone would use." +
    " For each: command run, exit code, time taken, pass/fail count. If anything is red, apply the smallest targeted fix (one root cause, not a rewrite) and re-run only that check. Do not refactor adjacent code. Do not add features. Do not delete tests to make them pass." +
    " If a check cannot run (missing tool, network-blocked registry, sandbox), say so explicitly with the reason — never claim 'green' by skipping." +
    " Stop when everything you ran is green, OR when you have a one-line list of what is provably red with the exact command and error. Either output is acceptable; guessing is not." +
    " No commentary. No recap. Output = the command results." +
    FINALIZE_FOOTER,

  /** Phase 3 (3/4): Persistence — commits, docs, TODO sweep, lockfiles. */
  finalizePersist: () =>
    "[auto-resume] Finalization mode (phase 3/4) — persistence pass. Make the work durable so the next session (or the user on a different machine) can resume cleanly without re-reading the whole conversation." +
    " In order, only doing what applies to this stack:" +
    " (1) Commit any uncommitted work in sensible units (one logical change per commit, message format the repo already uses — read 2 prior commits to match style). Skip the commit if the repo policy forbids auto-commits; in that case, print the exact git commands the user should run." +
    " (2) Update docs that drifted from code: README, CHANGELOG, API reference, config table, env-var table, run-book. Use the actual final state — no aspirational text." +
    " (3) Sweep for stale TODO/FIXME/HACK/XXX in the files you touched this session. Either resolve them or convert them to tracked issues (file + line + one-line summary). Never silently delete a TODO that signals a real follow-up." +
    " (4) Regenerate anything time-sensitive you touched: lockfiles, generated types, snapshot tests, golden files, schema dumps, index files." +
    " (5) Audit logs and stdout for leaked secrets/tokens/internal hostnames before they ship. If found, redact in place and add the exact scrubber rule that should have caught it." +
    " No new features. No 'while we're here' cleanups outside the files you touched. No drive-by refactors. If a step doesn't apply, say so in one line and move on." +
    FINALIZE_FOOTER,

  /** Phase 4 (4/4): Sign-off handoff message — DONE / VERIFIED / FOR YOU / CAVEATS. */
  finalizeSignoff: () =>
    "[auto-resume] Finalization mode (phase 4/4) — sign-off." +
    " Output ONE concise message with EXACTLY these four sections, in this order:" +
    " DONE: <bullet list of what is in the repo right now that wasn't before this session>" +
    " VERIFIED: <bullet list of commands you actually ran, with their pass/fail counts — never 'should be green'>" +
    " FOR YOU: <bullet list of manual steps the user must still do — PR creation, secret rotation, deploy button, anything not safe for an unattended agent>" +
    " CAVEATS: <bullet list of risks a reviewer should know — unverified assumptions, skipped checks with reasons, known follow-ups>" +
    " Keep each bullet to one line. No preamble. No recap of the conversation. No apology." +
    FINALIZE_FOOTER,

  /** Soft re-engage — fires when the user sends a new prompt after the
   *  model has produced its sign-off. */
  finalizeReengage: () =>
    "[auto-resume] Finalization overlay released — the user sent a fresh prompt. The session is back in normal drive mode. Continue the new request as a senior engineer would: production-grade, verified, no TODO/FIXME, no recap." +
    FINALIZE_FOOTER,

  /** Handsfree auto-proceed — fires when the user replies "yes", "go ahead",
   *  "handsfree", "auto-proceed", "y to all" to the model's proposal block.
   *  Distinct from finalizeAck because this is mid-conversation autopilot
   *  (NOT a finalization signal) — the plugin must NOT flip into the
   *  finalization overlay when the user is asking for handsfree work. */
  handsfreeYes: () =>
    "[auto-resume] Handsfree autopilot: the user replied 'yes / go / handsfree'. Continue autonomously with everything you just proposed or listed — including the WORKSPACE REFS update, the refactors, and any other follow-ups you named. No follow-up questions, no recap. Implement end-to-end at senior level: full impl + tests + error handling + doc touches, verified against the real toolchain (build/test/lint/typecheck). When every named follow-up is green, emit the same DONE / VERIFIED / FOR YOU / CAVEATS block. Aim above expectations.",
}