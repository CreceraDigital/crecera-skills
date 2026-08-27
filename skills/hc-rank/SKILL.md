---
name: hc-rank
description: Look up a domain's Harmonic Centrality (HC Rank / CC Rank) from Common Crawl's Web Graph — single or bulk — and use it to prioritize link building toward the web's link core. Reads Common Crawl's published domain-ranks file directly, so it does not depend on the (currently erroring) webgraph.metehan.ai tool. Triggers on "harmonic centrality", "HC rank", "CC rank", "crawl priority", "web core", "distance to core", "metehan webgraph", "AI visibility audit centrality check", or wanting to score/prioritize domains by proximity to the web core for link building.
---

# HC Rank — Harmonic Centrality from the Common Crawl Web Graph

Harmonic Centrality (HC) measures a domain's **proximity to the web's link core** — how few
hops, on average, it sits from everything else. Common Crawl uses HC to set **crawl priority**:
more-central domains are crawled deeper and more often, so more of their pages land in the
monthly archives that train LLMs (ChatGPT, Gemini, Claude, Perplexity). HC is *not* PageRank:
PageRank measures link *volume* (popularity); HC measures *distance to the core*. A single link
from a core-connected domain lifts centrality more than dozens from peripheral ones — which is
exactly why this matters for link building.

This skill reads Common Crawl's published **domain-level ranks file** directly. The community
tool **webgraph.metehan.ai** is just a front-end over the same data (and currently errors); going
to source never errors and scales to bulk lists.

## Quick start

```bash
PY=/c/Python314/python   # Windows python.org build

# 1) One-time per release (~2.35 GB download, cached OUTSIDE any cloud-synced folder).
#    duckdb is OPTIONAL and auto-skipped on Python 3.14 (it segfaults there); the
#    build still produces a working streaming-mode index and lookups run fine.
#    A crash in the optional parquet step can no longer strand the index.
$PY scripts/hc_rank.py build

# 2) Look up domains
$PY scripts/hc_rank.py lookup google.com bbc.co.uk yourclient.com

# 3) Bulk a prospect list -> XLSX (for the link-building tracker)
$PY scripts/hc_rank.py bulk prospects.txt --xlsx prospects_hc.xlsx

# Discover newer releases, then build a specific one
$PY scripts/hc_rank.py releases
$PY scripts/hc_rank.py build --release cc-main-2026-mar-apr-may
```

The cache lives at `%USERPROFILE%\.cache\cc-webgraph\` by default (override with the
`CC_WEBGRAPH_DIR` env var). **Never point it inside the cloud-synced tree** — it would try to sync
multiple GB.

## What you get per domain

| Field | Meaning |
|-------|---------|
| `hc_rank` (`harmonicc_pos`) | **The HC Rank.** 1 = most central. Lower = closer to the core = higher crawl priority. |
| `hc_value` | Raw harmonic centrality value (higher = more central). |
| `hc_percentile` | Position relative to all ~156M indexed domains. |
| `hc_grade` | Heuristic band (see below). |
| `pr_rank` / `pr_value` | PageRank position/value — shown for contrast, do not optimize for this. |
| `n_hosts` | Subdomains seen under the domain. |

### Grade bands (by HC rank position — documented heuristic)

| HC Rank | Grade | Read |
|--------:|-------|------|
| ≤ 10,000 | `A+ Web core` | Elite hubs (google, bbc, github…). |
| ≤ 100,000 | `A Near-core` | Strongly crawled; great link source. |
| ≤ 1,000,000 | `B Strong` | Healthy crawl priority. |
| ≤ 10,000,000 | `C Mid` | Crawled, but not prioritized. |
| ≤ 50,000,000 | `D Peripheral` | Shallow/infrequent crawling — a strategic risk. |
| otherwise | `E Edge` | Effectively stranded at the edge of the graph. |

## How HC is calculated (so you can explain it to clients)

For a domain *x*, harmonic centrality = **Σ over every reachable domain *y* of 1 / distance(x, y)**,
where distance is shortest-path hops in the host/domain link graph. Unreachable pairs contribute
0 (1/∞), so nodes close to *many* others score high. Common Crawl computes it on its ~300M-node
graph with the LAW **WebGraph** framework using **HyperBall / HyperANF** (a HyperLogLog
approximation of the neighbourhood function) — an approximation, refreshed roughly monthly, not
an exact all-pairs computation. Treat HC as a **directional** signal.

## The data (verified)

- Latest release: `cc-main-2026-mar-apr-may` (set in `LATEST_RELEASE` in the script).
- Domain ranks file (free, no auth, ~2.35 GB gz, ~156M domains):
  `https://data.commoncrawl.org/projects/hyperlinkgraph/<release>/domain/<release>-domain-ranks.txt.gz`
- TSV columns, sorted by `harmonicc_pos` asc:
  `harmonicc_pos  harmonicc_val  pr_pos  pr_val  host_rev  n_hosts`
- `host_rev` is the **reversed registered domain**: `com.google`, `uk.co.bbc` (= bbc.co.uk).
  The script reverses inputs via `tldextract` (handles multi-part suffixes like `.co.uk`).

See [`references/harmonic-centrality.md`](references/harmonic-centrality.md) for the full method,
the metehan.ai relationship, host-level option, and caveats.

## Using HC Rank in link building

A link's value for AI visibility scales with the **linking domain's** proximity to the core, not
just its DR/DA. Workflow:

1. **Client baseline** — `lookup yourclient.com` plus its competitors. The gap in HC Rank is the
   crawl-priority gap to close. Put it in the AI-visibility / link-building deliverable.
2. **Score prospects** — `bulk prospects.txt --xlsx ...`, then prioritize by HC grade. A
   `B`/`A`/`A+` linking domain transmits real core proximity; a `D`/`E` domain barely moves it
   even at high DR.
3. **Integrated** — the `backlink-research` skill calls this in its scoring phase and adds
   `HC Rank` + `HC Grade` columns to the prospect tracker (see that skill's Phase 3d).

**Raising a site's HC** = earn links from **core-connected** domains AND keep CCBot/AI crawlers
unblocked (robots.txt + WAF) so those new links are actually crawled. HC and crawl access are
complementary — a great link the crawler can't reach buys nothing.

## Notes & limits

- HC is an approximation, refreshed ~monthly — re-`build` when a newer release lands.
- Domain-level only (matches what metehan reports). Host-level is a future option.
- Pure-stdlib by default (gzip + csv) — **no required installs**. `tldextract` improves
  domain parsing, `openpyxl` enables XLSX, and `duckdb` (optional, non-3.14 only) adds a
  Parquet fast-path. All are best-effort; the skill runs without any of them.
- The build is download-bound (~2.35 GB once). In parquet mode lookups are sub-second;
  in streaming mode, core domains resolve in ~1s but a **NOT-FOUND / peripheral** domain
  scans the whole .gz (~5 min). For big prospect lists, run on a Python with duckdb
  (3.11/3.12) so `build` produces the Parquet, or expect longer bulk streaming passes.
