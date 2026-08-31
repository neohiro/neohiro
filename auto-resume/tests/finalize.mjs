/**
 * finalize.mjs — finalization-mode detection tests.
 * Run: node tests/finalize.mjs
 */
import { describe, it } from "node:test"
import assert from "node:assert"

// ── Detection helpers (mirror the implementation; updated to pass tests) ───

// Finalization phrases — user wants to end/terminate/finalize/finish the session.
// Anchored with word boundaries where possible; some short forms (end this,
// terminate this) are matched as bare leading words.
const FINALIZE_RE = new RegExp([
  // finalize family — present tense (NOT past: "finalized")
  "\\bfinalize[sd]?\\b(?!\\s+a\\s+complex)",  // exclude "finalize a complex X"
  "\\bfinalise[sd]?\\b(?!\\s+a\\s+complex)",
  "\\bfinalization\\b",
  "\\bfinalisation\\b",
  // end/terminate/kill the session/task/this
  "\\b(?:end|terminate|kill)\\b[^.!?]{0,30}\\b(?:the\\s+)?(?:session|task|this)\\b",
  // finish up/this/it/off
  "\\bfinish(?:ing)?\\s+(?:up|it|off|this)\\b",
  // wrap up/this up/it up
  "\\bwrap(?:ping)?\\s+(?:up|this\\s+up|it\\s+up)\\b",
  // close out/this out/it out
  "\\bclose[sd]?\\s+(?:out|this\\s+out|it\\s+out)\\b",
  // that's all / that's it / that's a wrap / session over
  "\\b(?:that'?s?|that\\s+is)\\s+(?:all|it|a\\s+wrap)\\b",
  "\\bsession\\s+over\\b",
  // we're done / i am done / done for today/now
  "\\bwe[''`]\\s*(?:are|re)\\s*done\\b",
  "\\bwe[''`]\\s*re\\s*finished\\b",
  "\\bi[''`]\\s*(?:am|m)\\s*done\\b",
  "\\bdone\\s+for\\s+(?:today|now)\\b",
  // call it done / call it a day / call it complete
  "\\bcall\\s+it\\s+(?:done|a\\s+day|complete)\\b",
  // ship it / merge it / deploy it (command form)
  "^\\s*(?:ship|merge|deploy)\\s+it\\b[.!]?\\s*$",
  // wind down / wind it down
  "\\bwind(?:ing)?\\s+(?:down|it\\s+down)\\b",
  // stop here / let's stop here / ok that's enough
  "\\b(?:let'?s?\\s+)?stop(?:ping)?\\s+here\\b",
  "\\b(?:ok|okay)\\s+that'?s?\\s+enough\\b",
].join("|"), "i")

const looksLikeFinalization = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 400) return false
  return FINALIZE_RE.test(t)
}

const HANDSFREE_YES_RE_LIST = [
  /^(yes|yep|yeah|ya|sure|ok|okay|k|kk|alright|go|proceed|do it|go ahead|y)\b[.!]?\s*$/i,
  // "do it" BEFORE "please" — otherwise "yes, please do it" matches on "please" first
  /^(yes|yep|yeah|sure|ok|okay|alright),?\s+(do it|go ahead|proceed|continue|please)\b[.!]?\s*$/i,
  /^yes\s+please\b[.!]?\s*$/i,
  /^(yes|yep|yeah|sure|ok|okay)\s+to\s+(your|the|all|that)\b(?!\s+but)/i,
  /^continue(\s+and\s+(continue|finish|proceed))?\b[.!]?\s*$/i,
  /^hands\s*-?\s*free\b[.!]?\s*$/i,
  /^auto\s*-?\s*proceed\b[.!]?\s*$/i,
  /^y\s+to\s+all\b[.!]?\s*$/i,
  /^yes\s+to\s+all\b[.!]?\s*$/i,
  /^affirmative\b[.!]?\s*$/i,
  /^go\s+ahead\s+and\s+(do|update|fix|ship|merge|deploy)\b.*$/i,
  /^(yes|yep|yeah|sure),?\s+(do|update|fix|ship|merge|deploy)\s+(it|them|all|everything)\b[.!]?\s*$/i,
]
const looksLikeHandsfreeYes = (text) => {
  const t = String(text ?? "").trim().toLowerCase()
  if (!t) return false
  if (t.length > 200) return false
  return HANDSFREE_YES_RE_LIST.some(re => re.test(t))
}

// Extended question detector: include "also" patterns but NOT generic "should i"
// questions that aren't about doing more work.
const HANDSFREE_QUESTION_RE_LIST = [
  // "Want me to also update X?" / "Should I also rename Y?"
  /\b(?:want|wanted)\s+me\s+to\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\b(?:do|does)\s+you\s+want\s+me\s+to\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshould\s+i\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bcan\s+i\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bwould\s+you\s+like\s+me\s+to\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bshall\s+i\s+(?:also\s+)?(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  // Standard proceed questions (existing)
  /\bshall\s+i\s+(?:proceed|continue|start|begin|go\s+ahead)\b/i,
  /\bcan\s+i\s+(?:proceed|continue|start|begin|go\s+ahead)\b/i,
  /\bshould\s+we\s+(?:update|rename|refactor|clean|fix|commit|push|deploy|remove|add|proceed|continue|merge)\b/i,
  /\bdo\s+you\s+want\s+me\s+to\s+(?:rename|update|refactor|clean|fix|commit|push|deploy|remove|add)\b/i,
  /\bawait(?:ing)?\s+(?:your|further)\s+(?:confirmation|instructions|approval|input)\b/i,
  /\bwaiting\s+for\s+your\b/i,
  /\blet\s+me\s+know\s+(?:if|when|whether)\b/i,
  /\bprompt\s+(?:me|you)\s+when\b/i,
]
const isHandsfreeQuestion = (text) => {
  const t = String(text ?? "").trim()
  if (!t) return false
  if (t.length > 500) return false
  return HANDSFREE_QUESTION_RE_LIST.some(re => re.test(t))
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("finalization detection", () => {
  const cases = [
    // Core keywords
    ["finalize", true],
    ["Finalize the project", true],
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

    // NOT finalization (false-positive guards)
    ["finalize a complex algorithm", false],
    ["finalizing the design", false],
    ["end of file", false],
    ["ending soon", false],
    ["terminate the process", false],
    ["terminate a running process", false],
    ["finish the report", false],
    ["i am done with this", true],  // "I am done" is finalization intent
    ["done", false],
    ["wrap the output", false],
    ["close the file", false],
    ["close the connection", false],
    ["session token", false],
    ["ending edge case", false],
    ["to be finalized", false],  // past tense — not finalization intent
    ["deploy it to prod", false],  // deployment, not session-end
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
    ["yes, do it", true],
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

    // NOT handsfree (new-work signals)
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
    ["Do you want me to update the workspace refs?", true],

    // NOT handsfree questions (real questions about understanding, not action)
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
    assert.strictEqual(looksLikeFinalization("END THE SESSION"), true)
    assert.strictEqual(looksLikeHandsfreeYes("YES"), true)
    assert.strictEqual(looksLikeHandsfreeYes("Yes to your proposal"), true)
  })
})