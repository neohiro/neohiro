/**
 * finalize-constants.js — shared constants for finalization mode.
 * Imported by auto-resume.js and finalize-detect.js.
 */

const FINALIZE_VERSION = "1.14.0"

/** Finalization-intent phrases. Matched word-boundary, case-insensitive.
 *  Ordered loosely from most-emphatic to most-casual; order does NOT affect
 *  matching (they're unioned into one big regex). */
export const DEFAULT_FINALIZE_PHRASES = [
  // explicit "end the session/task"
  "end the session", "end this session", "end the task", "end this",
  "terminate the session", "terminate this", "kill the session",
  // finalize family
  "finalize", "finalise", "finalization", "finalisation",
  // finish family
  "finish up", "finish this", "finish it", "finish off", "finishing up",
  // wrap family
  "wrap up", "wrap this up", "wrap it up",
  // close family
  "close out", "close this out", "close it out",
  // explicit "that's all / we're done"
  "that's all", "that is all", "that's it", "that'll do",
  "we're done", "we are done", "we're finished",
  "i'm done", "i am done",
  "done for today", "done for now",
  // ship / deploy signals
  "ship it", "merge it", "deploy it",
  // colloquial "call it done"
  "call it done", "call it a day", "call it complete",
  // wind-down signals
  "wind down", "wind it down",
  // explicit session-over
  "session over", "that's a wrap",
  "let's stop here", "lets stop here", "stop here",
  "ok that's enough", "okay that's enough",
]

/** Compiled once: union of all phrases into a single alternation regex. */
export const FINALIZE_RE = new RegExp(
  "\\b(?:" + DEFAULT_FINALIZE_PHRASES
    .map(p => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|") + ")\\b",
  "i",
)

/** Handsfree "yes / go" replies — short, unambiguous. Used to auto-proceed
 *  on the model's proposal blocks WITHOUT flipping into finalization mode. */
export const HANDSFREE_YES_RE_LIST = [
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

/** Finalization stage IDs (0 = inactive, 1-4 = active phases). */
export const FINALIZE_PHASES = {
  INACTIVE: 0,
  ACK: 1,
  VERIFY: 2,
  PERSIST: 3,
  SIGNOFF: 4,
}

/** Glyphs for the 4 finalization phases. Distinct shapes (not just colors)
 *  so color-blind users and terminal-monochrome screens can tell them apart.
 *  Each phase has a one-glance meaning:
 *    🔎  = looking at the work (acknowledge / scope check)
 *    🛡️  = verifying (build/test/lint)
 *    📦  = persisting (commits / lockfiles / docs)
 *    🏁  = signing off (final message to the user)
 *  The leading-character convention matches STATUS_STYLE: the leading
 *  glyph REPLACES any prior leading glyph so only ONE shape shows at a
 *  time. Trailing bracket label disambiguates "phase 3 / 4". */
export const FINALIZE_STATUS_STYLE = {
  1: { glyph: "🔎", label: "finalizing · scoping" },
  2: { glyph: "🛡️", label: "finalizing · verifying" },
  3: { glyph: "📦", label: "finalizing · persisting" },
  4: { glyph: "🏁", label: "finalizing · sign-off" },
}