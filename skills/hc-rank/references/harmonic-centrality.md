# Harmonic Centrality — Reference

## Definition

Harmonic centrality of a node *x* in a graph:

```
H(x) = Σ  1 / d(x, y)        for all y ≠ x
       y
```

where `d(x, y)` is the shortest-path distance (number of hops) from *x* to *y*. Unreachable
pairs have `d = ∞`, contributing `0`. Nodes that are a short distance from **many** other nodes
score high. Unlike closeness centrality, harmonic centrality handles disconnected graphs cleanly
(no division-by-infinity blowups), which is why it suits the web graph.

**HC vs PageRank.** PageRank is a random-walk stationary distribution — it rewards being pointed
to by *many important* pages (link volume / popularity). HC rewards being *close to everything*
(proximity to the core). They correlate but diverge: a page can have moderate PageRank yet very
high HC if it sits near dense, well-connected hubs. Common Crawl publishes both; it **sorts the
ranks file by HC** and uses HC for crawl prioritization.

## How Common Crawl computes it

- Common Crawl builds host-level and domain-level **Web Graphs** from the hyperlinks in each
  crawl (and merges several months per release).
- Ranking uses the **Laboratory for Web Algorithmics (LAW)** stack from the University of Milan
  — the **WebGraph** framework and LAW library (Sebastiano Vigna et al.).
- HC is computed with **HyperBall** (a.k.a. HyperANF), which uses **HyperLogLog** counters to
  approximate the *neighbourhood function* of every node (how many nodes are reachable within
  *t* hops) without doing exact all-pairs shortest paths. From the neighbourhood function it
  derives harmonic centrality. This is what makes it tractable on a graph with hundreds of
  millions of nodes and billions of edges.
- **Consequence:** the published HC is an **approximation**, recomputed each release (~monthly /
  every few months). Use it as a directional signal, not a precise score. Small rank movements
  between releases are noise; order-of-magnitude differences are real.
- Common Crawl has used HC for crawl-budget prioritization since ~2017.

## The published data products

For a release `<R>` (e.g. `cc-main-2026-mar-apr-may`), under
`https://data.commoncrawl.org/projects/hyperlinkgraph/<R>/`:

### Domain level (`/domain/`) — what this skill uses
- `<R>-domain-vertices.txt.gz` — node id ↔ reversed registered domain.
- `<R>-domain-edges.txt.gz` — the link edges.
- `<R>-domain-ranks.txt.gz` — **the ranks file we read.** TSV, header row, sorted by
  `harmonicc_pos` ascending. ~2.35 GB gz, ~156M domains (2026-mar-apr-may).

  Columns (verified live 2026-06-02):
  ```
  harmonicc_pos   harmonicc_val   pr_pos   pr_val   host_rev   n_hosts
  1   2.949189E7   1   0.0159839...   com.googleapis   2924
  3   2.8517818E7  2   0.0126132...   com.google       47399
  108 1.6438657E7  169 0.0001423...   uk.co.bbc        342
  ```
  - `host_rev` = registered domain with labels **reversed** (`com.google`, `uk.co.bbc`).
  - `n_hosts` = number of hosts/subdomains under that domain.

### Host level (`/host/`) — future option
- Same trio but per host; ranks file has `host_rev` reversed *host* (`com.example.www`) and **no**
  `n_hosts` column. Use when you need subdomain-level granularity. Bigger files (~hundreds of M
  hosts).

## Looking up one domain by hand (no tooling)

Because the ranks file is sorted by HC value (not by name), a name lookup needs a scan. For a
handful of domains you can stream-grep (reads up to the whole file):

```bash
# reverse example.com -> com.example, then scan
curl -s "https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2026-mar-apr-may/domain/cc-main-2026-mar-apr-may-domain-ranks.txt.gz" \
  | gunzip | grep -P "\tcom\.example\t"
```

For anything repeatable or bulk, build the local Parquet index (this skill's `build`) and query
with DuckDB — sub-second per lookup, one scan for a whole prospect list.

## Relationship to webgraph.metehan.ai

`webgraph.metehan.ai` ("CC Rank Checker", by Metehan Yesilyurt) is an independent community
front-end that ingests this same Common Crawl Web Graph rank data (it indexes a subset, ~18M
domains) and returns a domain's Harmonic Centrality + CC Rank. It is **not** an official Common
Crawl product, and Common Crawl has said it plans to ship its own centrality tool. Since the
metehan tool currently errors on queries — and only covers a subset — reading the source ranks
file is both more reliable and more complete (full ~156M domains, every release).

## Caveats for client work

- **Approximation + cadence:** HyperBall estimate, refreshed per release. Re-build monthly-ish.
- **Domain vs host:** this skill is domain-level (matches metehan). Subdomain strategies need the
  host graph.
- **HC ≠ traffic, ≠ DR.** It predicts *crawl priority / training-data inclusion*, not rankings or
  sessions. Pair it with DR/DA (Ahrefs/DfSEO) and CC Index coverage for a full picture.
- **Access still gates everything.** A high-HC domain that blocks CCBot at robots.txt or the WAF
  still won't accumulate archive presence. Check crawl access alongside HC (PDF Check #1).

## Sources
- Common Crawl Web Graphs: https://commoncrawl.org/web-graphs
- cc-webgraph tooling: https://github.com/commoncrawl/cc-webgraph
- LAW / WebGraph + HyperBall: https://law.di.unimi.it/ (Vigna et al.)
- Release listing: https://index.commoncrawl.org/web-graphs-index.html
- Field guide: *The AI Visibility Audit*, Stephen Burns, Common Crawl Foundation (2026).
