# AI register: diagnostic taxonomy

Read this when `register_score.py` has flagged a draft, or when a draft scores well
but still reads wrong. The script covers what is countable. This covers what is not.

## Why lexical substitution does not work

Modern detectors are trained with **mirror prompting**: for every human document in
the corpus, an LLM generates a version of the *same document* — same topic, same
length, same register — and the classifier is trained on the pair. The explicit
purpose is to stop the model keying on subject matter or vocabulary, and force it
onto structural difference. Hard-negative mining then hunts for human documents the
classifier wrongly flags and retrains on those.

The consequence for editing: a word-swap pass ("never write *delve*, *leverage*,
*robust*") changes the axis the training method was designed to neutralise. It
improves how a draft reads to a person, which is worth doing, but it moves the
statistical fingerprint very little. Published evaluations of "humanised" model
output still show detection in the mid-90s.

So treat the blacklist as **editorial hygiene**, not as the mechanism. The mechanism
is below.

---

## Tier 1 — Distributional (the scorer measures these)

| Property | Machine shape | Human shape |
|---|---|---|
| Sentence length | Clusters 15–25 words, low variance | Bursty; a 4-word sentence beside a 45-word one |
| Paragraph length | Uniform 3–4 sentences | Wildly uneven; a one-line paragraph for emphasis |
| Discourse markers | Every joint signposted | Cuts without warning; juxtaposition carries it |
| Section length | Near-symmetrical | Asymmetric — attention follows interest |
| Specificity | "many organisations", "some studies" | Named client, exact figure, actual date |
| Hedging | Uniform mid-confidence throughout | Certain here, openly lost there |
| Lists of three | Constant tricolon | Two items, or five, or an awkward four |

## Tier 2 — Rhetorical (judge by eye)

**The false-balance close.** Model prose resolves. It surveys a tension and lands on
"both matter, in balance." Human argument often refuses to resolve, or resolves
lopsidedly because the writer actually believes one side.

**Restatement as conclusion.** A final paragraph that compresses the preceding
sections without adding anything. Humans usually end on the newest thought, not the
oldest.

**Defined-on-first-use everything.** Models introduce and gloss every term. Writers
in a domain drop jargon unexplained, misuse it casually, or use in-group shorthand
that assumes the reader is already inside.

**The absent negative.** Model drafts rarely say what they tried that failed, what
they still can't explain, or where the advice breaks. A piece with no failure mode
in it is almost always synthetic or thin.

**Uniform paragraph function.** Every paragraph does the same job: assert, support,
transition. Human paragraphs vary in kind — one argues, the next is pure anecdote,
the next is a single aside.

## Tier 3 — Epistemic (the durable layer)

These cannot be added by editing. They are properties of what the writer knows.

1. **A claim with a cost.** A position someone could reasonably be annoyed by, that
   the writer would have to defend. Model output is optimised to be unobjectionable,
   so this is the single hardest property to fake and the most reliable signal.

2. **Unexplained specifics.** A name, a date, a tool, a number dropped in without
   ceremony because the writer assumes it matters and doesn't stop to justify it.
   Not decorative detail — *load-bearing* detail the argument would collapse without.

3. **Asymmetric attention.** Three sentences on the obviously important thing,
   eleven on the small weird thing the writer finds interesting. Models allocate
   words proportional to topic importance. People allocate proportional to their own
   curiosity.

4. **Admitted ignorance.** "I don't know why this works." "I've never seen data that
   settles it." A specific, bounded thing the writer cannot explain.

5. **Digression that doesn't fully close.** A tangent taken because it was
   interesting, returned from imperfectly.

6. **Provenance.** Where the knowledge came from — a conversation, a mistake, a
   client engagement, a thing someone said in a meeting in March.

---

## Editing order

Work top-down, because the tiers are not independent — fixing Tier 3 usually fixes
Tier 1 as a side effect, while fixing Tier 1 alone produces prose with artificially
jittered sentence lengths and nothing to say.

1. **Tier 3 first.** What does this draft know that a model could not? If the answer
   is nothing, the draft's problem is not style. Stop editing and go get the
   specifics — the client name, the number, the thing that went wrong.
2. **Tier 2 next.** Cut the restatement close. Delete the balanced hedge. Let one
   section run long.
3. **Tier 1 last, and lightly.** Re-run the scorer. Fix what still flags. Do not
   chase the composite past roughly 0.75 — beyond that you are optimising against a
   classifier rather than for a reader, and the classifier retrains.

## What this is not for

The scorer is a **content-quality triage instrument**. A draft scoring 0.2 is
usually not "insufficiently disguised" — it is genuinely thin, and the flags name
the thinness precisely: no specifics, no position, no failure mode. That diagnosis
is the value.

If a draft is substantively AI-written and the goal is for a reader to believe
otherwise, no amount of Tier 1 editing makes that honest. That is a disclosure
question, not an editing one — and increasingly a client-contract question. Handle
it upstream.
