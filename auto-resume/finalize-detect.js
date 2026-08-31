/**
 * finalize-detect.js — finalization-mode detection functions.
 * Pure functions; no side effects; fully unit-testable.
 */
import {
  FINALIZE_RE,
  HANDSFREE_YES_RE_LIST,
  FINALIZE_PHASES,
  FINALIZE_STATUS_STYLE,
} from "./finalize-constants.js"

/** Returns true when text contains a finalization-intent phrase.
 *  False for text > 400 chars (prevents false positives on long prompts). */
export const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 400) return false
  return FINALIZE_RE.test(t)
}

/** Returns true when the user prompt is a short "yes / go ahead / handsfree"
 *  reply that should be auto-applied (handsfree autopilot) instead of blocking.
 *  Ignores longer replies like "yes but also do X" — those are new work signals. */
export const looksLikeHandsfreeYes = (text) => {
  const t = String(text ?? "").trim().toLowerCase()
  if (!t) return false
  if (t.length > 200) return false
  return HANDSFREE_YES_RE_LIST.some(re => re.test(t))
}

/** Extended question detector for handsfree autopilot.
 *  Extends QUESTION_PATTERNS with "Want me to also...?" patterns.
 *  These are questions the model asks AFTER proposing work (e.g. "Want me to
 *  also update workspace refs?"), which should auto-fire proceedOnAsk instead
 *  of waiting for the user. */
export const HANDSFREE_QUESTION_RE_LIST = [
  // Standard proceed questions
  /\bshall i\b/i, /\bshould i\b/i, /\bwould you like me\b/i,
  /\bdo you want me to\b/i, /\bwant me to\b/i,
  /\bcan i (proceed|continue|start|begin|go ahead)\b/i,
  /\bshould we\b/i, /\blet me know (if|when|whether)\b/i,
  /\bawait(ing)? (your|further) (confirmation|instructions|approval|input)\b/i,
  /\bwaiting for your\b/i, /\bprompt (me|you) when\b/i,
  // "also" questions — the key pattern for "Want me to also update X?"
  /\bwant me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bdo you want me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshould i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bcan i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bwould you like me to (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshall i (also\s+)?(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  // Generic also-also
  /\b(also|too|as well)\s+(update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
]

/** Returns true when the model output contains a question that should be
 *  auto-answered by the handsfree autopilot (NOT flipped into finalization mode).
 *  The key case: "Want me to also update workspace refs?" after a rename. */
export const isHandsfreeQuestion = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 500) return false
  return HANDSFREE_QUESTION_RE_LIST.some(re => re.test(t))
}

/** Returns the STATUS_STYLE entry for a given finalization phase number.
 *  Returns null for phase 0 (inactive). */
export const finalizeStatusStyle = (phase) => {
  if (!phase || phase === FINALIZE_PHASES.INACTIVE) return null
  return FINALIZE_STATUS_STYLE[phase] ?? null
}

/** Returns the next finalization phase number, or 0 if at the last phase. */
export const nextFinalizePhase = (currentPhase) => {
  const max = FINALIZE_PHASES.SIGNOFF
  if (!currentPhase || currentPhase >= max) return 0
  return currentPhase + 1
}

/** Returns the prompt function name for a given finalization phase. */
export const finalizePhasePromptKey = (phase) => {
  switch (phase) {
    case FINALIZE_PHASES.ACK:     return "finalizeAck"
    case FINALIZE_PHASES.VERIFY:  return "finalizeVerify"
    case FINALIZE_PHASES.PERSIST: return "finalizePersist"
    case FINALIZE_PHASES.SIGNOFF: return "finalizeSignoff"
    default: return null
  }
}