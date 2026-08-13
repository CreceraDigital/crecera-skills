---
name: keyword-guidelines
description: Produce a "Keyword Guidelines [keyword]" content brief for a target search query. Pulls top-10 SERP results via DataforSEO, parses each competitor page, then outputs content structure ranges, important terms with frequency ranges, questions to answer, deduped competitor topics, and topic-grouped facts. Drop-in replacement for Surfer SEO's content-editor export. Outputs a human-readable .txt and a structured JSON. Use whenever the user asks for keyword guidelines, content guidelines, a content brief, SEO content optimization targets, or word/heading/term counts for a target keyword.
---

# Keyword Guidelines

Drop-in replacement for Surfer SEO's content-editor guidelines export. Same output shape, different engine. Works entirely through DataforSEO MCP tools + a local Python analyzer + one LLM pass for fact extraction.

## Output contract

For a given keyword + location, produce two files in the working directory:

1. `Keyword Guidelines [{keyword}].txt` — human-readable brief, same paste format as Surfer's content-editor export. The keyword inside the brackets is the user's verbatim search query (not slugified — spaces are preserved).
2. `Keyword Guidelines [{keyword}].json` — structured equivalent for pipelines.

If a file with the same name already exists in the output directory, append a `(YYYY-MM-DD)` suffix before the extension (e.g. `Keyword Guidelines [internal communication] (2026-05-20).txt`) to avoid clobbering prior runs.

Both files contain five sections in this exact order:

- **CONTENT STRUCTURE** — character / image / heading / paragraph / word ranges (min–max across top 10)
- **IMPORTANT TERMS TO USE** — up to 300 terms (1–5 grams) with per-term usage frequency ranges
- **QUESTIONS TO ANSWER** — 4–10 direct questions pulled from SERP `people_also_ask` + question-shaped competitor H2/H3s
- **TOPICS TO COVER** — up to ~80 deduped competitor headings (all H1/H2/H3) + PAA, source-tagged. Mirrors Surfer's "Topics & Questions" panel. Each competitor topic shows a `(N×)` page-count when it appears across multiple competitors.
- **FACTS TO INCLUDE** — topic-grouped factual claims extracted from competitor content

The .txt format must exactly match the Surfer layout shown below — downstream tooling parses it positionally. The TOPICS TO COVER section is an extension beyond Surfer's native .txt export (Surfer exposes this in the UI but not the export); parsers that don't recognize it should skip it cleanly.

## Surfer .txt format (target)

```
## CONTENT STRUCTURE
* Characters: 8719 - 14037
* Images: 7 - 23
* Headings: 12 - 22
* Paragraphs: 24 - Infinity
* Words: 1333 - 1533

## IMPORTANT TERMS TO USE
_Make sure to include those as many times as stated._
* deskless workers: 33 - 57
* deskless workforce: 4 - 8
...

## QUESTIONS TO ANSWER
* What is a deskless employee?
* What is office peacocking?
...

## TOPICS TO COVER
_Drawn from competitor headings and People Also Ask. Pick the ones relevant to your angle._

### From People Also Ask
* What is a deskless employee?
* ...

### From competitor headings
* What Is Internal Communication? (And Why It's Important) (3×)
* 11 reasons why internal communication is important at work
* How to improve internal communications (2×)
* ...

## FACTS TO INCLUDE
_Facts are grouped by topics._
### Technology for Deskless Workers
* Fact A
* Fact B

### Job Satisfaction and Retention
* Fact A
...
```

Note: when the maximum paragraph count is unbounded relative to the median (Surfer's heuristic), emit `Paragraphs: N - Infinity`. Apply the same rule when max > 2× median.

## Inputs

- **keyword** (required) — the target search query, e.g. `deskless workers`
- **location_code** (optional, default `2840` US) — DataforSEO location code
- **language_code** (optional, default `en`)
- **output_dir** (optional, default current working directory)

## Workflow

### Step 1 — Fetch SERP

Call `mcp__dataforSEO__serp_organic_live_advanced` with the keyword. Pull the top 10 organic results. Capture the raw response to `_work/serp.json`.

From the same response, extract any `people_also_ask` items — these become Question candidates.

Filter the 10 URLs to remove obvious non-content matches before parsing:
- Skip YouTube, Reddit, LinkedIn, Twitter, Facebook (different content shapes)
- Skip PDFs (.pdf in URL)
- Skip homepages where the path is `/` (rare on commercial keywords but possible)

If filtering drops below 8 URLs, pull from positions 11–15 to backfill. You want 8–10 article-shaped competitors.

### Step 2 — Parse each competitor

For each surviving URL, call `mcp__dataforSEO__on_page_content_parsing` with `url` set to that URL. The response includes parsed page content, headings, and structural data.

Save each parsed result to `_work/pages/{slugified-url}.json`.

If a parse fails (timeout, blocked, 4xx), drop the URL and continue. Need ≥ 7 successful parses to proceed; below that, surface the issue and ask the user whether to widen the SERP pull.

### Step 3a — Count images (optional but recommended)

DataforSEO's markdown output strips `<img>` tags, so the analyzer can't count images from parsed page text. Run this helper to fetch each URL directly and count images in the main content area:

```
python scripts/count_images.py --urls _work/serp.json --out _work/image_counts.json
```

Skip this step if you don't care about the Images range — the rest of the brief is unaffected.

### Step 3b — Run the analyzer

```
python scripts/analyze.py --pages _work/pages --serp _work/serp.json --keyword "{keyword}" --out _work/analysis.json --image-counts _work/image_counts.json
```

Omit `--image-counts` if you skipped 3a. The analyzer produces structure ranges (trimmed: drops the lowest and highest sample when N≥8 to avoid outlier-driven wide ranges), term frequency ranges, question candidates, and the deduped topic list.

### Step 4 — Extract facts

This is the only LLM-driven step. Read the parsed body text from all surviving pages (cap at ~3K words per page to fit context) and call this prompt:

> Below is content from {N} top-ranking pages for the keyword "{keyword}". Extract factual claims — statistics, percentages, dollar figures, dated events, definitions, named methods, named sources. Skip opinions and generic advice. Group facts into 3–6 topic clusters that emerge naturally from the content. For each cluster, give it a short Title Case heading and 3–8 bullets. Each bullet must be a single complete sentence stating one fact, written in neutral encyclopedic voice. Do not cite the source page in the bullet — just state the fact.
>
> Output in this exact format:
> ```
> ### {Topic Heading}
> * Fact bullet 1.
> * Fact bullet 2.
> ```

Save the raw LLM output to `_work/facts.md`.

### Step 5 — Render outputs

```
python scripts/render.py --analysis _work/analysis.json --facts _work/facts.md --keyword "{keyword}" --out-txt "{output_dir}/Keyword Guidelines [{keyword}].txt" --out-json "{output_dir}/Keyword Guidelines [{keyword}].json"
```

Use the keyword verbatim inside the brackets — preserve spaces and the user's original casing. If the keyword contains any of `\\ / : * ? " < > |` (filesystem-reserved characters on Windows), replace them with `-` before writing. If the target file already exists, append a `(YYYY-MM-DD)` suffix before the extension.

### Step 6 — Report

In the chat reply, list:
- Both output file paths
- Top 10 URLs that were analyzed (and any dropped, with reason)
- Counts: terms extracted, questions found, fact clusters identified
- One-sentence sanity check: "Word range 1333–1533, 80 terms, 4 questions, 5 fact clusters — matches Surfer shape."

## Constraints

- **Top 10 is the default sample.** Don't go higher without the user asking — it doubles parse cost and Surfer itself defaults to 10.
- **N-gram range is 1–5.** Surfer extracts phrases like `transportation and manufacturing industries` and `lack of employee engagement` — capping at 3 misses these. The boundary stop-word filter (first/last token must be a content word) keeps noise out at the higher n-gram lengths.
- **Stop-word filter is aggressive.** Cut articles, prepositions, copulas, and SEO-junk words ("read more", "learn more", "click here"). The analyzer ships a built-in list — extend only if a brand-specific term keeps getting filtered.
- **Term must appear in ≥ 3 pages.** Single-page artifacts (one competitor's brand name, one outlier) do not belong in the export.
- **Frequency ranges are min–max occurrences across pages that contain the term.** Not average. Surfer's "33 - 57" means the lowest page using "deskless workers" used it 33 times and the highest used it 57 times.
- **Don't fabricate facts.** If a fact bullet doesn't appear in source content, drop it. The LLM step is extraction, not invention.

## Failure modes to watch

- **Cloudflare / bot blocks on parsing** — common on enterprise SaaS pages. The DataforSEO parser handles most but not all. If 3+ URLs fail, switch to `mcp__dataforSEO__on_page_instant_pages` as a fallback.
- **PAA absent from SERP** — some keywords return no `people_also_ask` block. In that case, mine questions from competitor H2/H3 text matching `^(What|How|Why|When|Where|Is|Are|Can|Do|Does|Should)\b`.
- **Term inflation from boilerplate** — site nav and footer text can inflate term counts. The analyzer attempts to strip nav/footer via heuristics (short repeated blocks across pages of the same domain) but it isn't perfect. If a term feels boilerplate-driven, manually drop it.
- **Empty fact clusters** — thin SERPs (forum-heavy, mostly Reddit / Quora) yield few extractable facts. Surface this in the report rather than padding with generic statements.

## When NOT to use this skill

- The user wants competitor *strategy* analysis (positioning, USPs, conversion angles) — use `competitor-positioning` instead.
- The user wants topical clusters across many keywords — use `topical-map-dfseo2`.
- The user wants to rewrite an existing page based on the SERP — use `snippet-rewrite` or `aeo-page-optimizer`.

This skill produces *targets*, not strategy. It's the thing you hand to a writer alongside the actual brief.
