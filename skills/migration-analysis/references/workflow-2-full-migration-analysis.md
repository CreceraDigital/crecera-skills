# Workflow 2 — Full Migration Analysis

**When:** Once the Screaming Frog export with integrated API data is available. Can run at baseline (pre-migration), during UAT, or post-launch.

**Purpose:** Comprehensive page-level migration plan — tiering, redirect mapping, keyword intelligence, link equity preservation, risk register.

---

## Required data files

### 1. Screaming Frog Export with API Data (required)

`screaming-frog-YYYY-MM-DD.csv`

Integrates:
- **GA4 API** (12 months traffic)
- **GSC API** (12 months search performance)
- **Ahrefs API** (backlinks, keywords, traffic estimates)

#### Required Screaming Frog columns
- URL, Status Code, Indexability
- Title 1, Meta Description 1, H1-1, H2-1
- Word Count, Readability, Crawl Depth
- Inlinks, Outlinks, External Outlinks
- Canonical Link Element, Redirect URL, Redirect Type
- Schema / Structured Data (if custom extraction configured)

#### Required GA4 columns
- Sessions, Users, Pageviews
- Engagement Rate, Average Engagement Time
- Bounce Rate, Entrances, Exits

#### Required GSC columns
- Impressions, Clicks, CTR, Average Position

#### Required Ahrefs columns
- Ahrefs Rank, URL Rating
- Referring Domains, Backlinks
- Organic Keywords, Organic Traffic
- Top Organic Keyword

### 2. Schema export (optional but recommended)

`schema-export-YYYY-MM-DD.csv` — URL, Type, Property, Value
- From: Screaming Frog → Structured Data → Schema.org → Export All

### 3. Inlinks export (optional but recommended)

`inlinks-export-YYYY-MM-DD.csv` — Source, Destination, Anchor Text, Link Position
- From: Screaming Frog → Bulk Export → Links → All Inlinks

---

## Getting started

Ask (or extract from the data) the following:

```
Site URL: ?
Screaming Frog crawl date: ?
API data date ranges:
  GA4: last [X] months ending [YYYY-MM-DD]
  GSC: last [X] months ending [YYYY-MM-DD]
  Ahrefs: as of [YYYY-MM-DD]
Business type: ? (Hospitality / E-commerce / Blog / B2B SaaS / etc.)
Migration goals: ? (Platform change / URL restructure / Consolidation / etc.)
New platform/CMS (if known): ?
Specific concerns: ?
Priority pages or sections: ? (revenue drivers, top rankers, etc.)
```

If the user says "just analyze this migration," extract from the data and proceed without blocking.

---

## Analysis process

### Phase 1 — Data integration & validation
- Merge all data sources by URL
- Identify data gaps and anomalies
- Confirm API date ranges align
- Calculate aggregate metrics (total pages, total sessions, total backlinks, total ranking KWs, etc.)
- Report any cross-source mismatches

### Phase 2 — Page segmentation
Categorize each page by:
- Content type (homepage, hub, leaf, blog, location, product, etc.)
- Performance tier (top quintile vs long tail)
- SEO value (rankings, backlinks, link equity)
- User engagement (engagement rate, time on page)
- Technical health (indexability, redirect chains, canonicals)

### Phase 3 — Keyword intelligence
For each significant page:
- Top ranking keywords
- Branded vs non-branded split
- Search volume + difficulty
- Keyword cannibalization (multiple pages targeting same cluster)
- Seasonal patterns where detectable

### Phase 4 — Content quality assessment
- Thin content (low word count + low engagement)
- Duplicate content (similar pages / cannibalization candidates)
- Content gaps vs competitors (where Ahrefs data shows competitor pages outranking)
- High traffic + poor engagement (optimization opportunities)
- Orphaned pages with backlinks (link equity at risk)

### Phase 5 — Link equity mapping
- Pages with highest internal link equity (inlinks × source authority)
- External backlink concentration (which pages hold the link value)
- Redirect chains and loops
- Orphan pages carrying backlink value

### Phase 6 — Decision matrix

| Tier | Criteria | Action | Priority |
|---|---|---|---|
| **1 — Must Migrate** | Top 20% traffic OR high conversions OR 10+ ranking keywords OR 5+ quality backlinks | Preserve exactly, minimal URL changes | Critical |
| **2 — Migrate with Improvements** | Moderate traffic/rankings, optimization opportunity | Migrate with content enhancement | High |
| **3 — Consolidate** | Multiple weak pages targeting similar keywords, thin content with some value | Merge into stronger pages, 301 redirect | Medium |
| **4 — Redirect or Remove** | No traffic, no rankings, no backlinks, thin/outdated | 301 to relevant page or 410 | Low |

### Phase 7 — Risk assessment & quick wins

**High-risk pages (flag prominently):**
- Top 10 traffic pages
- Pages with 50+ backlinks
- Pages ranking positions 1–3 for non-branded terms
- High conversion pages

**Quick wins:**
- Missing meta descriptions on high-traffic pages
- Thin content that can be expanded pre-migration
- Broken internal links
- Missing schema where competitors have it

---

## Deliverables

1. **Executive Summary** — total pages, tier distribution, estimated risk, headline recommendations
2. **Page-Level Migration Plan (CSV)** — URL, tier, action, new URL recommendation, priority score, top KWs, traffic, backlinks, notes
3. **Consolidation Opportunities** — page groups to merge, target pages, content to preserve
4. **Risk Register** — highest-risk pages with specific factors and mitigation strategies
5. **Keyword Cannibalization Report** — clusters targeted by multiple pages
6. **Technical SEO Priorities** — redirect chains, schema opportunities, internal linking improvements
7. **Content Improvement Roadmap** — pages needing expansion pre-migration, content gaps, competitor advantages

---

## URL recommendation heuristics

When proposing new URLs:
- Preserve URL slug if there's no business reason to change it
- If consolidating, the strongest page (by backlinks, then rankings, then traffic) is the target URL
- Keep depth ≤ 3 for high-value pages
- Avoid pluralization changes (item → items) without a redirect plan
- Don't change trailing-slash convention site-wide without a global 301 rule

## Priority scoring formula (simple)

```
priority = (sessions_norm * 0.35)
         + (organic_kw_count_norm * 0.25)
         + (referring_domains_norm * 0.20)
         + (engagement_rate * 0.10)
         + (clicks_norm * 0.10)
```

`*_norm` = min-max normalized within the dataset. Adjust weights for business context (e.g., heavier `referring_domains` weight for content-heavy sites, heavier `sessions` weight for transactional sites).
