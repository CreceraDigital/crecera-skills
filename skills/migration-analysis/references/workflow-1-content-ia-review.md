# Workflow 1 — Pre-Migration Content & IA Review

**When:** As soon as the development partner provides the project status workbook with content and IA decisions — typically well before redirects or meta tags are defined.

**Purpose:** Flag SEO risks in content and site structure decisions *before* they get locked in. Early detection layer.

---

## Required file

**Project Status Workbook (.xlsx)** — multi-tab tracker from the dev partner.

Expected tabs (presence varies by project):
- Site Content
- Accommodations
- Offers
- Venues
- FAQs
- Activities
- Events
- Blogs
- Press
- Ranking KWs (Ahrefs export)
- SF Scan (Screaming Frog crawl of current live site)
- UAT Feedback
- Launch Checklist

### Critical tabs

| Tab | What it gives you |
|---|---|
| **Site Content** | Proposed IA, page hierarchy, current URLs, keyword targets, content status, recommended new URLs, legacy meta titles/descriptions |
| **Ranking KWs** | Current rankings with volume, position, ranking URL, intent (typically Ahrefs export) |
| **SF Scan** | Current site crawl — word count, inlinks, indexability, schema |
| Content tabs (Accommodations / Offers / etc.) | Actual copy being written for the new site |

---

## Getting started

1. Load the workbook and enumerate tab names + column headers for each critical tab.
2. Report what was found and what's missing.
3. Ask which output the user wants:
   - **A.** Bulleted risk list (shareable with dev partner / client)
   - **B.** Page-by-page risk audit spreadsheet (working doc)
   - **C.** Both

Default to **A** unless the user has indicated they want the working doc.

---

## Analysis checklist

### 1. IA structure mapping
- Extract full proposed page hierarchy from Site Content
- Map every proposed page → current URL equivalent (or flag as new)
- Identify current-site URLs that don't appear in the new IA

### 2. Content-to-rankings cross-reference
- Compare keyword targets in Site Content vs actual ranking data in Ranking KWs
- Flag pages where the assigned KW target doesn't match what the page ranks for now
- Identify high-ranking URLs that are being restructured or consolidated

### 3. Page merging & consolidation risks
- Flag any case where multiple current URLs map to a single new page
- For each, note which of the current URLs carry ranking keywords, inlinks, or substantial content
- Flag where consolidation needs explicit redirect planning

### 4. Content quality checks
- Scan approved copy for typos and spelling errors
- Check room/accommodation descriptions for geographic signals (city/destination name) and brand mentions
- Flag approved/in-review pages missing critical SEO elements
- Identify sections with no content status set — these may launch empty

### 5. New page assessment
- List all proposed pages with no current site equivalent
- Flag new sections (Wellness, Membership, Spa, etc.) where the property may not have enough real content to support multiple pages
- Identify thin content risk for pages being broken out from existing combined pages

### 6. Missing or orphaned pages
- Cross-reference SF Scan URLs against the proposed IA
- Flag current pages with significant inlinks or ranking keywords that aren't accounted for in the new structure

---

## Output format

### Option A — Bulleted risk list

Organize into two sections, written for the dev partner / client:

```
## Content Issues
- [Specific page or section]: [problem] — [recommended action]
- ...

## IA / Page Merging Concerns
- [Specific URL or section]: [problem] — [recommended action]
- ...
```

Keep entries:
- Specific (name the page, not "some pages")
- Actionable (what should the dev partner do?)
- Free of SEO jargon where possible — most readers are not SEOs

### Option B — Page-by-page audit spreadsheet

One row per proposed new page. Merges Site Content + Ranking KWs + SF Scan into a single working view.

Suggested columns:
- New page name / path
- Recommended URL
- Current URL equivalent(s)
- Content status
- Word count (current)
- Inlinks (current)
- Top ranking keywords (current URL)
- Position / volume for top KW
- KW target (from Site Content) — match flag vs actual rankings
- Risk flags (consolidation / orphan / thin / missing copy / KW mismatch / no content status)
- Notes

Color-code or sort by risk severity.

### Option C — Both

Produce both deliverables. Lead with the bulleted list (the thing they'll actually read), follow with the audit XLSX (the working doc).

---

## Common dev-partner findings

- "Approved" copy with city / brand name absent (hospitality)
- Same KW target assigned to 3+ different proposed pages (cannibalization built in)
- Three current /weddings, /events, /private-events URLs collapsing into one new /gather page with no redirect column
- New /membership section spec'd as 6 pages, source brand has 1 page of real content
- Current /restaurants/[name] pages with strong non-brand rankings being merged into one /dining page
- SF Scan shows /press URLs ranking, but no Press section exists in the new IA
