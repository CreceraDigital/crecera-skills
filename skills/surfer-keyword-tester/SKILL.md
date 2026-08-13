---
name: surfer-keyword-tester
description: Test each Surfer Important Term against an article to predict which will lift the Surfer Content Editor score, then suggest natural placements for the winners. Reads the article (Google Doc URL, .docx, or pasted text), parses Surfer's pasted Important Terms list with target frequency ranges, counts current occurrences, ranks each candidate by predicted score lift, and outputs specific before/after sentence rewrites showing where to incorporate each kept term. Use whenever the user wants to raise their Surfer score, decide which Surfer keywords are worth adding, batch-test Surfer Important Terms, find placements for content brief terms, or push a Surfer score above 80.
---

# Surfer Keyword Tester

Replaces the manual "paste-keywords-at-top-of-doc-and-watch-the-Surfer-score" loop. The user normally adds candidate Surfer terms to a test list at the top of the article, watches the Content Editor score, keeps the ones that lift it, drops the rest, then incorporates the survivors into prose. This skill does that loop in one shot — locally — by reading Surfer's term targets and the article text, and producing a ranked placement plan.

## Output contract

Produce a single file in the working directory:

`Surfer Keyword Test [{article_title}].md` — a markdown report with these sections in this order:

1. **Summary** — baseline term-compliance score, projected score if all suggestions are applied, number of gap / compliant / over terms.
2. **Suggested placements (kept terms)** — for each gap term ranked by predicted lift, a block showing target range, current count, additions needed, predicted lift, and 1–3 specific placement suggestions with section heading + before/after sentences.
3. **Already compliant** — terms in target range, no action.
4. **Reduce frequency (over-stuffed)** — terms above max, with current count and how many to cut.
5. **Could not place** — gap terms where no natural placement could be found in the existing article context (these are honest misses, not silent drops).

If a file with the same name exists in the output directory, append a `(YYYY-MM-DD)` suffix before the extension.

## Inputs

- **article** (required) — one of: a Google Doc URL, a `.docx` file path, or pasted article text. The Google Doc URL is the primary expected input since articles are authored in Google Docs with Surfer attached.
- **surfer_terms** (required) — a pasted block from Surfer's Important Terms panel. The parser is lenient about format (colon, pipe, tab, or whitespace separators; en-dashes or hyphens; bulleted or unbulleted).
- **target_score** (optional, default 80) — the Surfer score the user is aiming for. Used to decide when to stop suggesting additions.
- **output_dir** (optional, default current working directory).

## Workflow

### Step 1 — Gather article text

If the article input is a Google Doc URL:
- Call `mcp__google-drive__readGoogleDoc` (or `mcp__claude_ai_Google_Drive__read_file_content` if the first MCP isn't connected) to fetch the doc body.
- Capture the doc title — it's the `{article_title}` used in the output filename.
- Strip any existing "test keyword list" the user has at the top of the doc, so it doesn't bias the count. Heuristic: if the doc opens with a bulleted or comma-separated list of bare terms before the first prose paragraph or heading, drop it. Otherwise leave the doc alone.

If `.docx`: extract text via `python-docx` (already in the environment). If pasted: use as-is.

Write the cleaned article text to `_work/article.txt`.

### Step 2 — Capture Surfer terms

Write the user's pasted Surfer Important Terms block verbatim to `_work/terms.txt`. Do not pre-process — the Python parser handles format variation.

### Step 3 — Run the scorer

```
python scripts/score.py --article _work/article.txt --terms _work/terms.txt --out _work/report.json --target-score {target_score}
```

The scorer produces `_work/report.json` containing:
- `baseline_score` — current term-compliance score (0–100)
- `projected_score_if_all_applied` — score after bringing every gap term to its min
- `gap_terms` — terms below min, ranked by predicted lift (each has: term, min, max, current, additions_needed, lift)
- `compliant_terms` — terms in range, no action
- `over_terms` — terms above max, with `excess` count

The score is a **term-compliance score**, not Surfer's full 0–100 (which also weighs word/heading/paragraph counts). It tracks Surfer's *direction of change* very closely because the user's keyword-test loop only touches term frequencies — structural signals don't change. Report the score with that caveat in the Summary section.

### Step 4 — Find placements for kept gap terms

For each gap term in the ranked list, call Claude (this is the LLM-driven step inside the skill — do it as part of skill execution, not via a subprocess) with this prompt:

> The following article needs to incorporate the term **"{term}"** {additions_needed} more time(s) to satisfy a Surfer content brief (target range: {min}–{max} occurrences, currently {current}).
>
> Find {additions_needed} natural placement(s) in the article where this term can be added or substituted in without sounding stuffed or breaking flow. For each placement:
> 1. Quote the **nearest H2 or H3 section heading** so the user can locate it.
> 2. Show the **BEFORE** sentence (exact text from the article, verbatim).
> 3. Show an **AFTER** sentence with the term incorporated. Prefer minimal edits — substituting a generic noun phrase ("the platform", "the tool") with the target term is ideal. Only insert a new clause when no substitution opportunity exists.
> 4. Briefly explain why this placement reads naturally (one sentence).
>
> If you cannot find any natural placement (the article context simply doesn't support this term), say so explicitly. Do not force placements that read awkwardly — the user prefers an honest "no fit" over forced prose.

For terms where no placement fits, list them in the **Could not place** section of the output rather than dropping them silently. They're still candidates Surfer flagged — the user may decide to restructure a section to accommodate, or to drop the term from their target list.

Batch placements: call the model once per term, or batch 5–10 terms per call if the article is short. Don't batch the entire term list — Claude needs to see each placement decision in context.

### Step 5 — Render the report

Compose the markdown report following the **Output contract** section. Use this template per kept term:

```markdown
### {n}. "{term}" — predicted lift +{lift} pts
**Current:** {current} occurrences  |  **Target:** {min}–{max}  |  **Additions needed:** {additions_needed}

**Placement A** — in section "{section_heading}"
> **BEFORE:** {before_sentence}
>
> **AFTER:** {after_sentence}
>
> {one-sentence rationale}

**Placement B** — ...
```

Save to `{output_dir}/Surfer Keyword Test [{article_title}].md`.

### Step 6 — Report in chat

Summarize in the chat reply:
- Output file path
- Baseline → projected score
- Counts: N gap terms with placements, N already compliant, N over-stuffed, N could-not-place
- Whether projected score reaches the target

If the projected score is still below `target_score`, flag it: the user may need to revisit structural signals (word count, headings) which this skill does not address.

## Constraints

- **Term matching is case-insensitive, whole-phrase, word-boundary-anchored.** "deskless workers" matches both "Deskless workers" and "deskless workers" but not "deskless workerss". Overlapping terms (e.g. "deskless" and "deskless workers") are counted independently — this matches Surfer's behavior.
- **The score is term-compliance only, not the full Surfer score.** Report it as such. The user cares about *lift direction* (will adding this term help?), which this model captures faithfully. Absolute parity with Surfer's number is not promised.
- **Suggest minimum edits.** Prefer substituting a generic phrase ("the platform" → "the deskless workforce platform") over inserting new sentences. Surfer doesn't care how the term arrives; the user does care about prose quality.
- **No silent drops.** Every gap term either gets placements, lands in "compliant" (because the scorer already saw it was in range), or lands in "could not place" with a one-line reason.
- **Do not auto-edit the Google Doc.** Output is a plan, not a write. The user applies edits themselves so they can sanity-check each one against the live Surfer score.

## Failure modes to watch

- **Surfer paste with weird formatting** — if the parser extracts zero terms, surface the raw input and ask the user to confirm the format. Common cause: the user copied a screenshot region with line breaks inside terms.
- **Google Doc fetch failure** — Drive MCP can return empty content for docs that are still loading or have permission issues. Verify the doc text length is > 200 chars before proceeding; otherwise stop and ask.
- **All terms already compliant** — surfaces as a Summary with no gap terms. Tell the user their article is already term-compliant per Surfer's targets and the low Surfer score likely comes from structural signals (word count, headings, paragraph count, images).
- **Massive gap list (>40 gap terms)** — the article is far below Surfer's targets. Don't generate 40+ placements; cap at the top 20 by predicted lift and tell the user the rest will need a rewrite, not insertions.
- **Term is a brand or product name not used in the article** — the scorer doesn't know to flag this. If placements come back as "could not place" for several consecutive terms, mention to the user that the SERP-derived term list may include competitor brand terms that don't belong in their article.

## When NOT to use this skill

- The user wants to generate the Surfer-style targets themselves (no Surfer subscription) — use `keyword-guidelines` to produce the term list first, then feed its output into this skill.
- The user wants a full content rewrite, not term insertion — use `aeo-page-optimizer` or `snippet-rewrite`.
- The user wants to understand why their Surfer score is low when terms are all compliant — that's a structural issue (word count / headings); this skill does not address it.
- The user wants real-time integration with Surfer's actual scoring API — this skill uses local approximation. A future variant could use Playwright or Surfer's API.
