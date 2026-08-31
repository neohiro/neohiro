/**
 * finalize.test.mjs — tests for finalization mode.
 * Run: node tests/finalize.test.mjs
 */
import { describe, it } from "node:test"
import assert from "node:assert"

// ── Helpers imported from the plugin (inline copies for test isolation) ──────

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

const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 400) return false
  return FINALIZE_RE.test(t)
}

const looksLikeHandsfreeYes = (text) => {
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

// ── Handsfree "yes to proposal" patterns ───────────────────────────────────

const HANDSFREE_QUESTION_PATTERNS = [
  /\bshall i\b/i, /\bshould i\b/i, /\bwould you like me\b/i,
  /\bdo you want me to\b/i, /\bwant me to\b/i,
  /\bcan i (proceed|continue|start|begin|go ahead)\b/i,
  /\bshould we\b/i, /\blet me know (if|when|whether)\b/i,
  /\bawait(ing)? (your|further) (confirmation|instructions|approval|input)\b/i,
  /\bwaiting for your\b/i, /\bprompt (me|you) when\b/i,
  /\bwant me to (also|also update|also fix|also clean up)\b/i,
  /\bwant me to (rename|update|refactor|clean|fix|commit|push|deploy)\b/i,
]

const isHandsfreeQuestion = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 500) return false
  return HANDSFREE_QUESTION_PATTERNS.some(re => re.test(t))
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("finalization detection", () => {
  const cases = [
    // Core keywords
    ["finalize", true],
    ["finalize the project", true],
    ["let's finalize", true],
    ["finalise the changes", true],
    ["finalization mode", true],
    ["end the session", true],
    ["end this", true],
    ["end the task", true],
    ["terminate the session", true],
    ["terminate this", true],
    ["kill the session", true],
    ["finish up", true],
    ["finish this", true],
    ["finish it", true],
    ["finish off", true],
    ["wrap up", true],
    ["wrap this up", true],
    ["wrap it up", true],
    ["close out", true],
    ["close this out", true],
    ["close it out", true],
    ["that's all", true],
    ["that's it", true],
    ["we're done", true],
    ["we are done", true],
    ["i'm done", true],
    ["i am done", true],
    ["done for today", true],
    ["done for now", true],
    ["ship it", true],
    ["merge it", true],
    ["deploy it", true],
    ["call it done", true],
    ["call it a day", true],
    ["call it complete", true],
    ["wind down", true],
    ["wind it down", true],
    ["session over", true],
    ["that's a wrap", true],
    ["let's stop here", true],
    ["lets stop here", true],
    ["stop here", true],
    ["ok that's enough", true],
    ["okay that's enough", true],

    // NOT finalization
    ["finalize a complex algorithm", false],
    ["finalizing the design", false],
    ["end of file", false],
    ["ending soon", false],
    ["terminate the process", false],
    ["terminate a running process", false],
    ["finish the report", false],
    ["we're done with that", false],
    ["i am done with this", false],
    ["done", false],
    ["wrap the output", false],
    ["close the file", false],
    ["close the connection", false],
    ["that is all i need", false],
    ["session token", false],
    ["ending edge case", false],
    ["to be finalized", false],
    ["finalisation process", false],
    ["deploy it to prod", false],
    ["", false],
    ["  ", false],
  ]

  for (const [input, expected] of cases) {
    it(`${JSON.stringify(input)} → ${expected}`, () => {
      assert.strictEqual(looksLikeFinalization(input), expected,
        `looksLikeFinalization(${JSON.stringify(input)}) should be ${expected}`)
    })
  }
})

describe("handsfree 'yes' detection", () => {
  const yesCases = [
    ["yes", true],
    ["y", true],
    ["yep", true],
    ["yeah", true],
    ["ya", true],
    ["sure", true],
    ["ok", true],
    ["okay", true],
    ["k", true],
    ["alright", true],
    ["go", true],
    ["proceed", true],
    ["do it", true],
    ["go ahead", true],
    ["yes please", true],
    ["yes, please do it", true],
    ["yes, go ahead", true],
    ["yes, proceed", true],
    ["yes to your proposal", true],
    ["yes to all, continue handsfree", true],
    ["yes to all", true],
    ["yes to that", true],
    ["continue", true],
    ["continue and finish", true],
    ["hands-free", true],
    ["hands free", true],
    ["auto-proceed", true],
    ["auto proceed", true],
    ["y to all", true],
    ["affirmative", true],
    ["nope", false],
    ["no", false],
    ["maybe", false],
    ["not yet", false],
    ["later", false],
    ["hmm", false],
    ["interesting", false],
    ["not sure", false],
    ["", false],
    ["yes but also do X", false],
    ["yes to all but Y", false],
    ["ok maybe also Z", false],
    ["sure thing", false],
  ]

  for (const [input, expected] of yesCases) {
    it(`${JSON.stringify(input)} → ${expected}`, () => {
      assert.strictEqual(looksLikeHandsfreeYes(input), expected,
        `looksLikeHandsfreeYes(${JSON.stringify(input)}) should be ${expected}`)
    })
  }
})

describe("handsfree question detection", () => {
  const qCases = [
    // Standard proceed questions
    ["Should I also update the workspace refs?", true],
    ["Do you want me to also update workspace refs?", true],
    ["Want me to also update the workspace refs?", true],
    ["Should I rename neohiro/achievement-hacks?", true],
    ["Do you want me to rename it?", true],
    ["Want me to also fix that?", true],
    ["Can I proceed with the rename?", true],
    ["Should we update the registry?", true],
    ["Would you like me to commit?", true],
    ["Shall I push?", true],
    ["Do you want me to clean up?", true],

    // NOT handsfree questions (shouldn't block)
    ["What is the capital of France?", false],
    ["How does this work?", false],
    ["Why did this fail?", false],
    ["Where is the config file?", false],
    ["Can you explain the error?", false],
    ["What should I do next?", false],
    ["Should I be worried?", false],
    ["Should finalize mode be on?", false],
    ["", false],
  ]

  for (const [input, expected] of qCases) {
    it(`${JSON.stringify(input)} → ${expected}`, () => {
      assert.strictEqual(isHandsfreeQuestion(input), expected,
        `isHandsfreeQuestion(${JSON.stringify(input)}) should be ${expected}`)
    })
  }
})

describe("edge cases", () => {
  it("truncates very long input", () => {
    const long = "x".repeat(500)
    assert.strictEqual(looksLikeFinalization(long), false)
  })

  it("handles null/undefined", () => {
    assert.strictEqual(looksLikeFinalization(null), false)
    assert.strictEqual(looksLikeFinalization(undefined), false)
    assert.strictEqual(looksLikeHandsfreeYes(null), false)
    assert.strictEqual(looksLikeHandsfreeYes(undefined), false)
    assert.strictEqual(isHandsfreeQuestion(null), false)
    assert.strictEqual(isHandsfreeQuestion(undefined), false)
  })

  it("case insensitive", () => {
    assert.strictEqual(looksLikeFinalization("FINALIZE"), true)
    assert.strictEqual(looksLikeFinalization("Finalize"), true)
    assert.strictEqual(looksLikeFinalization("FINALIZE THE SESSION"), true)
    assert.strictEqual(looksLikeHandsfreeYes("YES"), true)
    assert.strictEqual(looksLikeHandsfreeYes("Yes to your proposal"), true)
  })
})

console.log("F1: finalization detection")
console.log("F2: handsfree yes detection")
console.log("F3: handsfree question detection")
console.log("F4: edge cases")
console.log("All finalize test patterns defined.")
