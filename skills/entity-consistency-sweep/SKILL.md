---
name: entity-consistency-sweep
description: Off-site consistency audit for the corroboration/parametric AI-visibility layer — the off-site mirror of extraction-audit. Harvests how the web actually describes a client across third-party surfaces (Gumshoe LLM outputs/citations, DataForSEO business listings + brand SERP, key profiles like Crunchbase/PitchBook/G2/Capterra/LinkedIn/Wikidata), diffs each against the client's Canonical Entity Kit (correct category, canonical facts, comparison set, descriptor), and produces a severity-ranked remediation list (tracker-compatible W5 rows) plus a consistency score. Because inconsistent/wrong third-party descriptions dilute the parametric pattern, this finds and prioritizes the fixes that matter — weighted by surface authority and extractability (crawl → corpus). Triggers on "entity consistency sweep", "W5 sweep", "where does the web describe [client] wrong", "off-site consistency audit", "find inconsistent/stale descriptions", "wrong category on third-party profiles", "consistency remediation list", or auditing corroboration quality. Requires a Canonical Entity Kit (run canonical-entity-kit first), the Gumshoe API, DataForSEO MCP, and a scraper (firecrawl/brightdata). Feeds the corroboration tracker; pairs with canonical-entity-kit, gumshoe-citation-targets, and journalist-outreach. Always use this skill — do not eyeball consistency by hand.
---

# Entity Consistency Sweep (W5)

`extraction-audit` checks whether *your own pages* are machine-readable. This checks whether *the rest of the web* describes you **correctly and consistently** — because on the parametric side, a wrong category or stale fact repeated across trusted surfaces is what the model's next training snapshot will encode. The sweep finds those, ranks them by damage, and turns them into remediation work.

Program context: `AI and Automation/Corroboration Layer Playbook/`. Rationale: `parametric-vs-retrieval-framing` memory.

## When to use
After a CEK exists, and on a quarterly cadence, to find where third parties misdescribe the client. Also whenever a baseline measurement shows the model asserting a wrong fact/category and you need to trace it to live sources.

## Prerequisite
The client's **Canonical Entity Kit** (ground truth). If none, run `canonical-entity-kit` first — you cannot judge consistency without the SSOT.

## Workflow

### Phase 1 — Harvest descriptions (how the web/LLMs describe the client)
- **LLM layer:** run/read a Gumshoe report — how models describe the client and which sources they cite. Note category, facts asserted, and associations.
- **Structured web:** DataForSEO `business_data_business_listings_search` + `serp_organic_live_advanced` for brand queries → knowledge-panel / listing framing.
- **Key third-party profiles:** scrape (firecrawl/brightdata) Crunchbase, PitchBook, G2, Capterra, LinkedIn, Wikidata/Wikipedia, top industry directories. For each, capture: **category filed under, one-line description, canonical facts stated, comparison set / entities it's placed beside.**

### Phase 2 — Diff each surface against the CEK
For every surface score: category match (Y/N), each canonical fact match (Y/N/stale), comparison-set match, descriptor drift. Assign **severity**:
- **High** — wrong category or a false/stale canonical fact on a high-authority, crawlable surface (feeds corpus and Google graph).
- **Med** — drift on a mid-authority surface, or right facts but wrong comparison set.
- **Low** — cosmetic / low-authority / uncrawlable surface.
Weight severity by **surface authority × extractability** (an uncrawlable wrong page is lower priority — the corpus can't read it anyway; confirm with `bot-crawl-check` on borderline cases).

### Phase 3 — Classify remediation
Per finding: **self-serve edit** (we control/can edit) · **submit correction** (form/request, e.g. PitchBook/Crunchbase) · **outreach to fix** (editorial — route to `journalist-outreach`) · **monitor** (uneditable, low severity) · **Wikidata fix** (route to `wiki-scout`). Map each to acquisition ease.

### Phase 4 — Output
- **`[Client]-consistency-sweep-[date].csv`** — W5 remediation rows, tracker-compatible (surface, current framing, CEK-correct framing, severity, remediation type, owner, ease). Drop straight into the corroboration tracker.
- **`[Client]-consistency-brief-[date].md`** — findings ranked by severity×authority×extractability, plus a **consistency score** = % of audited surfaces matching the CEK on category + core facts. Track it over time.

## Caveats
- **LLM output ≠ live web.** A wrong description in a model's answer may be *historical corpus* — fix the live sources, then re-measure over training cycles; don't expect an instant flip. The live-surface fixes are the lever; the LLM output is the lagging indicator.
- Some surfaces are uneditable or slow (PitchBook, third-party editorial) — correction-submit or outreach, and accept lag.
- Consistency score is directional (surface set is a sample, not the whole corpus) — keep the audited surface list stable release-to-release so the trend is comparable.
- Prioritize crawlable + high-authority first; that's where the parametric payoff concentrates.
