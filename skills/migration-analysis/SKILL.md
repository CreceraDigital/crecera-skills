---
name: migration-analysis
description: Two-workflow migration risk analysis for site rebuilds and replatforms. Workflow 1 (pre-migration) ingests a development partner's project status workbook (a multi-tab .xlsx) and flags content + IA risks before redirects exist — page merging, missing rankings coverage, thin new sections, orphaned current URLs, copy quality, schema/local signals. Workflow 2 (full migration) ingests a Screaming Frog export with integrated GA4 + GSC + Ahrefs API data and produces a tiered page-level migration plan with redirect mapping, keyword cannibalization, link-equity preservation, and a risk register. Use when the user mentions a site migration, replatform, redirect plan, project status workbook, IA review, Screaming Frog migration export, page consolidation, pre-launch SEO risk, or asks "analyze this migration."
---

# Migration Analysis

Two analysis workflows for different stages of a migration project. Pick by the file the user uploads, not by asking.

| Workflow | Trigger file | Stage | Primary output |
|---|---|---|---|
| **1. Pre-Migration Content & IA Review** | Multi-tab project status workbook (.xlsx) from dev partner — has tabs like Site Content, Ranking KWs, SF Scan, Accommodations, Offers, Venues, FAQs, Activities, Events, Blogs, Press, UAT Feedback, Launch Checklist | Early — content + IA decisions being made, redirects not yet defined | Bulleted risk list (shareable with dev partner / client) ± page-by-page audit XLSX |
| **2. Full Migration Analysis** | Single Screaming Frog export (.csv) with integrated GA4 + GSC + Ahrefs API columns | Any — baseline, UAT, post-launch | Tiered page-level migration plan with redirect mapping, risk register, consolidation map |

---

## Workflow selection

When the user uploads a file:

1. **Multi-tab .xlsx with "Site Content" or "Ranking KWs" tab → Workflow 1.** Read `references/workflow-1-content-ia-review.md` in full.
2. **Single .csv with `Title 1`, `Sessions`, `Impressions`, `Ahrefs Rank` style columns → Workflow 2.** Read `references/workflow-2-full-migration-analysis.md` in full.
3. **Ambiguous** — auto-detect tab/column structure first, then confirm with the user.

If the user names a workflow explicitly ("run the content review", "do the full migration analysis"), skip detection.

---

## Workflow 1 — fast path

After loading the workbook, ask which output:

- **A.** Bulleted risk list only (email/Slack ready) — fastest, ~80% of value
- **B.** Page-by-page audit spreadsheet (working doc)
- **C.** Both

Critical tabs: **Site Content** (proposed IA + URLs + KW targets), **Ranking KWs** (Ahrefs export), **SF Scan** (current crawl), and content tabs (Accommodations / Offers / etc.).

Risk categories to flag — see `references/workflow-1-content-ia-review.md` for the full checklist. The headline ones:

- **IA orphans** — current URLs with rankings or inlinks that have no destination in the new IA
- **Silent consolidations** — multiple current URLs collapsing into one new page with no redirect note
- **KW/page mismatches** — page is targeting keyword X but currently ranks for Y
- **Thin new sections** — Wellness / Membership / Spa style sections expanded to multiple pages without source content
- **Copy gaps** — accommodation/restaurant copy missing geographic + brand signals
- **Empty placeholder pages** — sections with no content status that will launch blank
- **Typos** in approved copy

Output is written to be **shared directly with the dev partner or client**. Keep it specific, free of SEO jargon, actionable.

---

## Workflow 2 — fast path

Confirm context quickly:

```
Site URL: ?
SF crawl date: ?
API ranges (GA4 / GSC / Ahrefs): ?
Business type: ?
Migration goals: ?
Priority sections / concerns: ?
```

If the user says "just analyze this migration," extract from the data and proceed.

Then run the seven phases (see `references/workflow-2-full-migration-analysis.md` for full detail):

1. Data integration & validation
2. Page segmentation
3. Keyword intelligence
4. Content quality assessment
5. Link equity mapping
6. Decision matrix tiering (Tier 1 Must Migrate / Tier 2 Migrate with Improvements / Tier 3 Consolidate / Tier 4 Redirect or Remove)
7. Risk assessment + quick wins

Deliverables:
- Executive summary
- Page-level migration plan (CSV) — URL, tier, action, new URL recommendation, priority score, top KWs, traffic, backlinks, notes
- Consolidation opportunities map
- Risk register (Tier-1 + 50+ backlink pages + non-brand top-3 rankers)
- Keyword cannibalization report
- Technical SEO priorities (redirect chains, schema, internal linking)
- Content improvement roadmap

---

## Domain handling

If the site is a hospitality property (hotel, resort, restaurant group), also read `references/hospitality-special-handling.md`. Room/accommodation thin-page sprawl, restaurant page ranking equity, and local + brand signal preservation are the recurring traps.

For other verticals, apply the same principles to their equivalent landing-page systems (e-commerce category pages, B2B SaaS use-case pages, etc.).

---

## Analysis principles (apply to both workflows)

- **Data over opinions** — base decisions on metrics, not assumptions
- **Traffic preservation** — when in doubt, protect existing traffic
- **Revenue and conversions outweigh volume** — high-converting pages need protection even at modest traffic
- **Traffic concentration is the primary risk lens** — top 5–10 pages typically carry 90%+ of value
- **Missing redirects are more dangerous than imperfect ones** — gaps are the highest-priority fix
- **Content that looks like blog posts can be landing pages** — always cross-reference engagement data before recommending removal
- **Link equity matters** — external backlinks are precious, don't waste them
- **Simplification is good** — fewer, better pages outperform sprawl
- **Thin content on key landing pages is a pre-launch blocker**

---

## Development partner workflow note (the dev partner pattern)

Typical sequence:
1. Content written and approved
2. IA defined in the project tracker
3. Meta titles, descriptions, recommended URLs come later
4. Redirects arrive days before launch

**Workflow 1 is the primary leverage point.** By the time redirects arrive, content and IA are locked. Catching issues at the content approval stage is what changes outcomes.

Watch list in these workbooks:
- Content approved without keyword cross-referencing
- New sections expanded beyond what the property can support with real content
- Multiple current URLs being consolidated without explicit redirect notes
- Current pages with significant rankings or inlinks that don't appear in the new IA
- Placeholder sections with no content status
- Copy missing geographic and brand signals (hospitality especially)

---

## Data validation (both workflows)

When files arrive, automatically check:
- Presence of expected tabs/columns
- Data completeness (missing values, null fields)
- URL format consistency (trailing slashes, http vs https, www)
- Total page count vs crawl completeness
- Cross-referencing between sources — ranking URLs that don't appear in the SF crawl, GSC URLs not in the workbook, etc.

Flag any issues before producing the analysis.
