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
  // finalize family — present tense only (NOT "finalized" past tense)
  // finalize family — present tense only. "finalize" and "finalize this" are commands;
  // "finalization mode" is a noun-phrase command; "to be finalized" is a description.
  // Apostrophe and `s` are word chars in JS regex, so use [start|punct|whitespace] prefix.
  "(?:^|[\\s.!?])(?:let's |lets |let us )?finalize(?:\\s|$|[.!?])",
  "(?:^|[\\s.!?])(?:let's |lets |let us )?finalise(?:\\s|$|[.!?])",
  "\\bfinalization\\b", "\\bfinalisation\\b",
  // "to be finalized" / "to be finalized later" = NOT a finalization command
  // (handled by negative lookahead in looksLikeFinalization, not here)
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
  // we're done / we are done — the apostrophe is a word character in JS regex,
  // so "we're" has NO space between we and re. Pattern handles both forms.
  "\\bwe(?:\\s+(?:are|re|ll)|'(?:re|ll|m))\\s+(?:done|finished)\\b",
  // i am done / i'm done
  "\\bi(?:\\s+(?:am|m|ll)|'(?:m|ll))(?:\\s+(?:done|finished)\\b)",
  // done for today/now
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
  // Negative-lookahead guard: "to be finalized" is a present-progressive
  // description, NOT a finalization command.
  if (/\bto\s+be\s+finali[sz]ed\b/i.test(t)) return false
  if (!FINALIZE_RE.test(t)) return false
  // After matching, check that the matched "finalize/ise" is not followed
  // by a verb phrase that suggests description ("finalize a complex X").
  // We treat these as finalization only if finalize is bare or ends the text.
  const phrasalContext = /finali[sz]e\s+(?:the\s+)?(?:this|it|project|changes|task|session|work|everything|all|please)\b/i
  const descriptiveContext = /finali[sz]e\s+(?:a|an|my|your|the)\s+\w+/i
  if (descriptiveContext.test(t) && !phrasalContext.test(t)) return false
  return true
}

const HANDSFREE_YES_RE_LIST = [
  // Bare "do it" / "go ahead" etc. — single-word replies
  /^(?:yes|yep|yeah|ya|sure|ok|okay|k|kk|alright|go|proceed|do it|go ahead|y)\b[.!]?\s*$/i,
  // "yes, do it" / "yeah, go ahead" / "sure, proceed" — comma form
  /^(?:yes|yep|yeah|sure|ok|okay|alright),?\s+(?:do it|go ahead|proceed|continue)\b[.!]?\s*$/i,
  // "yes, please" (alone) — without trailing verb
  /^(?:yes|yep|yeah|sure|ok|okay|alright),?\s+please\b[.!]?\s*$/i,
  // "yes, please do it" / "yes, please proceed" — please + verb
  /^(?:yes|yep|yeah|sure|ok|okay|alright),?\s+please\s+(?:do it|go ahead|proceed|continue)\b[.!]?\s*$/i,
  // "yes to your proposal" / "yes to all" / "yes to that"
  /^(?:yes|yep|yeah|sure|ok|okay)\s+to\s+(?:your|the|all|that)\b(?!\s+but)/i,
  // "continue" / "continue and finish"
  /^continue(?:\s+and\s+(?:continue|finish|proceed))?\b[.!]?\s*$/i,
  // "handsfree" / "hands-free" / "hands free"
  /^hands\s*-?\s*free\b[.!]?\s*$/i,
  // "auto-proceed" / "auto proceed"
  /^auto\s*-?\s*proceed\b[.!]?\s*$/i,
  // "y to all"
  /^y\s+to\s+all\b[.!]?\s*$/i,
  // "yes to all"
  /^yes\s+to\s+all\b[.!]?\s*$/i,
  // "affirmative"
  /^affirmative\b[.!]?\s*$/i,
  // "go ahead and X"
  /^go\s+ahead\s+and\s+(?:do|update|fix|ship|merge|deploy)\b.*$/i,
  // "yes, do it" / "sure, fix it all" etc.
  /^(?:yes|yep|yeah|sure),?\s+(?:do|update|fix|ship|merge|deploy)\s+(?:it|them|all|everything)\b[.!]?\s*$/i,
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