# Crecera Skills

Public, scrubbed versions of [Claude Code](https://claude.com/claude-code) skills we use
day to day at [Crecera Digital](https://creceradigital.com) — SEO, AEO, content and
general engineering workflow.

These are the real skills, not demos. What's been removed is client data and
machine-specific detail, nothing else. See [What's been scrubbed](#whats-been-scrubbed).

## Install

### As a plugin (recommended)

This repo is a plugin marketplace. Inside Claude Code:

```
/plugin marketplace add https://github.com/CreceraDigital/crecera-skills.git
/plugin install crecera-skills@crecera
```

That installs all twelve. They're namespaced under the plugin, so they appear as
`/crecera-skills:roast`, `/crecera-skills:humanizer` and so on — no collisions with
skills you already have. If the install summary says `Run /reload-plugins to activate`,
run that.

To update later, `/plugin marketplace update crecera`. To remove,
`/plugin uninstall crecera-skills@crecera`.

<details>
<summary>Using <code>owner/repo</code> shorthand instead</summary>

`/plugin marketplace add CreceraDigital/crecera-skills` also works, but GitHub
shorthand clones over SSH by default. Use the full `.git` URL above unless you have SSH
keys set up for GitHub, or set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.
</details>

### Copying a single skill

A skill is just a folder with a `SKILL.md` in it, so you can take one on its own:

```bash
git clone --depth 1 https://github.com/CreceraDigital/crecera-skills.git
cp -r crecera-skills/skills/roast ~/.claude/skills/
```

Or grab a [zip of the repo](https://github.com/CreceraDigital/crecera-skills/archive/refs/heads/main.zip)
and copy the folders you want out of `skills/`.

Use `~/.claude/skills/` to install for yourself across every project, or
`.claude/skills/` inside a project to scope it to that repo. On Windows the personal
path is `%USERPROFILE%\.claude\skills\`. Installed this way the skill keeps its plain
name — `/roast`, not `/crecera-skills:roast`.

Restart Claude Code, then confirm with `/help`. You mostly won't need to type the
names: skills trigger from their `description`, so describing the task is enough.

## The skills

| Skill | What it does | Needs |
| --- | --- | --- |
| [`roast`](skills/roast) | Convenes a 5-persona adversarial council to attack an idea, then a Judge returns one GO / RESHAPE / KILL verdict and the cheapest test to de-risk it. Antidote to Claude agreeing with you. | — |
| [`humanizer`](skills/humanizer) | Scores a draft on structural fingerprints of machine writing (burstiness, signpost density, specificity, epistemic range) and repairs them. Ships a Python scorer and a calibration workflow for per-brand weight profiles. | Python 3 |
| [`session-handoff`](skills/session-handoff) | Structured end-of-session summary — decisions, shipped changes, running state, deferrals, open questions — so a fresh context can pick up cleanly. Chat-only, writes nothing. | — |
| [`goal`](skills/goal) | Runs a task autonomously toward an explicit definition of done, self-driving until the condition is met. | — |
| [`email-strategy`](skills/email-strategy) | Email promotion strategy plus ready-to-send copy: launches, flash sales, webinars, price increases, BFCM, promo sequences. | — |
| [`keyword-guidelines`](skills/keyword-guidelines) | Content brief for a target query — structure ranges, term frequency ranges, questions, competitor topics and grouped facts. A drop-in replacement for Surfer's content-editor export. | DataForSEO |
| [`surfer-keyword-tester`](skills/surfer-keyword-tester) | Tests each Surfer Important Term against an article to predict which will actually lift the Content Editor score, then suggests natural placements for the winners. | Surfer export |
| [`hc-rank`](skills/hc-rank) | Looks up a domain's Harmonic Centrality from Common Crawl's Web Graph, single or bulk, to prioritise link building toward the web's link core. Reads the published ranks file directly — no paid API. | Python 3, ~2.4 GB download |
| [`migration-analysis`](skills/migration-analysis) | Two-workflow migration risk analysis for rebuilds and replatforms: pre-migration content/IA risk from a project status workbook, then a tiered page-level plan with redirect mapping and a risk register. | Crawl + GA4/GSC exports |
| [`codex`](skills/codex) | Hands a plan, diff or question to the OpenAI Codex CLI for a second opinion, with multi-turn sessions. | Codex CLI |
| [`entity-consistency-sweep`](skills/entity-consistency-sweep) | Off-site consistency audit — harvests how third-party surfaces describe a brand, diffs each against a canonical entity kit, and ranks the remediations that matter. ¹ | Gumshoe, DataForSEO, scraper |
| [`framer-code-components`](skills/framer-code-components) | Framer code component constraints, layout annotations, property controls and authoring practice. ² | Framer |

¹ ² These two are companion skills to internal ones we haven't published. They still
read as useful reference, but they won't run end to end out of the box:
`entity-consistency-sweep` expects a canonical entity kit as input, and
`framer-code-components` is written to be loaded by a parent `framer` skill.

## What's been scrubbed

Everything under `skills/` is generated by [`scripts/scrub.py`](scripts/scrub.py) from
our working copies. The scrub removes:

- **Client identities** — names, domains and initials, in prose and in code comments.
- **Client corpora** — calibration sets, run outputs, and any spreadsheet or document
  data. `humanizer` ships its calibrated weight profile but not the client articles it
  was derived from; build your own with `--calibrate`.
- **Machine-specific paths** — absolute user paths become `~`, and Windows separators
  inside them are normalised.
- **Credentials** — no keys, tokens or `.env` files are copied, and the build fails if
  anything key-shaped appears.

The rules live in [`scripts/scrub-rules.json`](scripts/scrub-rules.json) so you can see
exactly what was rewritten and why — every rule carries a `_why`.

The last step is a leak scan over the built tree against a list of client names,
credential shapes and path patterns. It exits non-zero on any hit, and it runs in CI on
every push, so a redaction miss fails the build rather than shipping.

```bash
python scripts/scrub.py            # rebuild everything
python scripts/scrub.py humanizer  # rebuild one skill
python scripts/scrub.py --check    # scan the tree, copy nothing
```

Don't edit files under `skills/` — `scrub.py` overwrites them. Change the source skill
or the rules.

## Notes

Skills are model-invoked: Claude reads the `description` in each `SKILL.md` and decides
when to load it. If one isn't triggering, the description is usually the thing to edit —
make it name the situations and phrases you'd actually use.

Several of these lean on paid APIs (DataForSEO, Ahrefs, Gumshoe) or exports from tools
like Surfer and Screaming Frog. The workflow logic is still worth reading even without
them, and most are straightforward to repoint at a different data source.

## Licence

[MIT](LICENSE). Use them, fork them, adapt them. No warranty — read a skill before you
run it, especially the ones that spend API credits.
