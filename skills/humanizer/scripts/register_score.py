#!/usr/bin/env python3
"""
register_score.py — measure the structural fingerprints that make prose read as
machine-generated, independent of vocabulary.

Rationale: detectors trained with mirror-prompting (Pangram et al.) deliberately
neutralise topic, length and lexical choice, because every human sample is paired
with an AI sample on the same subject. What survives that normalisation is
distribution: sentence-length variance, signpost density, epistemic flatness,
specificity. Those are what this scores.

This is a triage instrument, not a verdict. It tells you which drafts to look at,
and which axis is thin. Thresholds ship deliberately conservative — calibrate them
against your own corpus with --calibrate before trusting the flags.

Usage:
    python register_score.py draft.md
    python register_score.py draft.md --json
    python register_score.py --calibrate ./corpus/human ./corpus/ai
    cat draft.md | python register_score.py -

No third-party dependencies.
"""

import argparse
import json
import math
import os
import re
import statistics
import sys
from collections import Counter

# Windows terminals default to cp1252 and will crash printing the report's
# non-ASCII glyphs. Force UTF-8 where the runtime allows; the report itself is
# also kept ASCII-safe below so it degrades cleanly if this fails.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# --------------------------------------------------------------------------
# Lexicons. These are NOT the detection mechanism — they are cheap proxies for
# structural properties. Edit freely; the metric shapes matter more than the
# exact word lists.
# --------------------------------------------------------------------------

SIGNPOSTS = {
    "however", "moreover", "furthermore", "additionally", "consequently",
    "therefore", "thus", "ultimately", "importantly", "notably", "crucially",
    "indeed", "essentially", "fundamentally", "significantly", "similarly",
    "conversely", "meanwhile", "overall", "specifically", "particularly",
    "nevertheless", "nonetheless", "accordingly", "subsequently",
}

SIGNPOST_PHRASES = [
    "that said", "with that in mind", "building on", "in essence", "at its core",
    "it is worth noting", "it's worth noting", "keep in mind", "as a result",
    "in other words", "more importantly", "on the other hand", "in contrast",
    "by contrast", "in summary", "in conclusion", "to put it simply",
    "the key takeaway", "what this means", "let's break", "lets break",
    "at the end of the day", "when it comes to", "in today's", "in the realm of",
]

ABSTRACT = {
    "landscape", "realm", "framework", "approach", "approaches", "aspect",
    "aspects", "consideration", "considerations", "dynamic", "dynamics",
    "paradigm", "ecosystem", "journey", "tapestry", "nuance", "nuances",
    "insight", "insights", "strategy", "strategies", "solution", "solutions",
    "capability", "capabilities", "methodology", "opportunity", "opportunities",
    "challenge", "challenges", "initiative", "initiatives", "synergy",
    "leverage", "robust", "seamless", "holistic", "comprehensive", "pivotal",
    "testament", "underscore", "underscores", "delve", "crucial", "vital",
    "essential", "innovative", "cutting-edge", "transformative", "myriad",
    "plethora", "multifaceted", "intricate", "profound", "unprecedented",
    "streamline", "streamlined", "optimize", "empower", "empowering",
    "foster", "fostering", "navigate", "navigating", "harness", "unlock",
    "elevate", "amplify", "bolster", "facilitate", "utilize", "utilise",
}

HEDGES = {
    "may", "might", "could", "can", "often", "typically", "generally",
    "usually", "somewhat", "relatively", "arguably", "potentially", "largely",
    "various", "several", "numerous", "many", "some", "certain", "likely",
    "perhaps", "possibly", "roughly", "fairly", "quite", "rather",
}

HIGH_CERTAINTY = [
    "always", "never", "must", "definitely", "certainly", "undeniably",
    "without question", "no doubt", "obviously", "clearly wrong", "flatly",
    "categorically", "guaranteed", "impossible", "the answer is",
    "i'm certain", "i am certain", "unambiguously",
]

OPEN_UNCERTAINTY = [
    "i don't know", "i do not know", "no idea", "unclear", "unsure",
    "can't tell", "cannot tell", "still figuring", "baffl", "puzzl",
    "i'm not sure", "i am not sure", "we don't know", "we do not know",
    "beats me", "hard to say", "who knows", "i suspect", "my guess",
    "haven't worked out", "havent worked out", "remains a mystery",
]

# --------------------------------------------------------------------------
# Text segmentation
# --------------------------------------------------------------------------

ABBREV = r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bSt)(?<!\bvs)(?<!\be\.g)(?<!\bi\.e)(?<!\betc)"
SENT_SPLIT = re.compile(ABBREV + r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z\"'(\[])")
WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
CODE_FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`]+`")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HEADER = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$", re.M)
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+", re.M)


def strip_markdown(text):
    text = CODE_FENCE.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = MD_LINK.sub(r"\1", text)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    return text


def prose_body(text):
    """Drop headers and list items — they have their own length conventions and
    would otherwise crush the sentence-variance signal."""
    lines = []
    for line in strip_markdown(text).splitlines():
        if HEADER.match(line):
            continue
        if LIST_ITEM.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def sentences(text):
    out = []
    for para in paragraphs(text):
        flat = re.sub(r"\s+", " ", para).strip()
        out.extend(s.strip() for s in SENT_SPLIT.split(flat) if s.strip())
    return out


def words(text):
    return WORD.findall(text)


# --------------------------------------------------------------------------
# Metrics. Each returns (value, score) where score is 0..1 and HIGHER = more
# human-shaped. Keeping the direction consistent makes the composite readable.
# --------------------------------------------------------------------------

def _cv(values):
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    if mean == 0:
        return 0.0
    return statistics.pstdev(values) / mean


def _band(value, low, high):
    """Map a value onto 0..1, saturating outside [low, high]."""
    if high == low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def m_sentence_burstiness(ctx):
    lengths = [len(words(s)) for s in ctx["sents"]]
    lengths = [n for n in lengths if n > 0]
    cv = _cv(lengths)
    return cv, _band(cv, 0.35, 0.70)


def m_paragraph_burstiness(ctx):
    lengths = [len(words(p)) for p in ctx["paras"]]
    lengths = [n for n in lengths if n > 0]
    cv = _cv(lengths)
    return cv, _band(cv, 0.25, 0.65)


def m_short_sentence_share(ctx):
    """Fragments and punchy one-clause sentences. AI formal prose almost never
    drops below ~8 words; humans do it for rhythm."""
    lengths = [len(words(s)) for s in ctx["sents"]]
    if not lengths:
        return 0.0, 0.0
    share = sum(1 for n in lengths if n <= 7) / len(lengths)
    return share, _band(share, 0.02, 0.18)


def m_signpost_density(ctx):
    """Share of sentences that open with an explicit discourse marker."""
    sents = ctx["sents"]
    if not sents:
        return 0.0, 0.0
    hits = 0
    for s in sents:
        low = s.lower().lstrip("\"'([ ")
        first = WORD.match(low)
        if first and first.group(0) in SIGNPOSTS:
            hits += 1
            continue
        if any(low.startswith(p) for p in SIGNPOST_PHRASES):
            hits += 1
    density = hits / len(sents)
    # inverted: lower density is more human
    return density, 1.0 - _band(density, 0.03, 0.20)


def m_opener_diversity(ctx):
    """Normalised entropy of sentence-opening words."""
    sents = ctx["sents"]
    if len(sents) < 4:
        return 0.0, 0.0
    firsts = []
    for s in sents:
        m = WORD.search(s)
        if m:
            firsts.append(m.group(0).lower())
    if not firsts:
        return 0.0, 0.0
    counts = Counter(firsts)
    total = sum(counts.values())
    ent = -sum((c / total) * math.log2(c / total) for c in counts.values())
    max_ent = math.log2(len(counts)) if len(counts) > 1 else 1.0
    norm = ent / max_ent if max_ent else 0.0
    return norm, _band(norm, 0.75, 0.97)


def m_specificity(ctx):
    """Concrete referents per 100 words: figures, dates, money, proper nouns.
    The single most reliable human tell in nonfiction — models generalise,
    people cite the actual thing."""
    body = ctx["body"]
    toks = ctx["words"]
    if not toks:
        return 0.0, 0.0
    numerals = len(re.findall(r"\b\d[\d,.]*\b", body))
    pct = len(re.findall(r"\d+\s?%|\bpercent\b", body))
    money = len(re.findall(r"[$£€]\s?\d", body))
    years = len(re.findall(r"\b(?:19|20)\d{2}\b", body))
    # proper nouns: capitalised tokens that are not sentence-initial
    propn = 0
    for s in ctx["sents"]:
        tokens = WORD.findall(s)
        for t in tokens[1:]:
            if t[0].isupper() and not t.isupper():
                propn += 1
    per100 = (numerals + pct + money + years + propn) / len(toks) * 100
    return per100, _band(per100, 1.0, 7.0)


def m_abstraction_load(ctx):
    toks = [w.lower() for w in ctx["words"]]
    if not toks:
        return 0.0, 0.0
    hits = sum(1 for w in toks if w in ABSTRACT)
    per100 = hits / len(toks) * 100
    return per100, 1.0 - _band(per100, 0.4, 3.0)


def m_hedge_density(ctx):
    toks = [w.lower() for w in ctx["words"]]
    if not toks:
        return 0.0, 0.0
    hits = sum(1 for w in toks if w in HEDGES)
    per100 = hits / len(toks) * 100
    return per100, 1.0 - _band(per100, 2.0, 7.0)


def m_epistemic_range(ctx):
    """Human writing is confident about some things and openly lost about others.
    Model output sits at a uniform ~70% confidence throughout. Reward presence of
    BOTH poles; a text with neither is flat, which is the tell."""
    low = ctx["body"].lower()
    hi = sum(1 for p in HIGH_CERTAINTY if p in low)
    un = sum(1 for p in OPEN_UNCERTAINTY if p in low)
    per1k = (hi + un) / max(len(ctx["words"]), 1) * 1000
    both = 1.0 if (hi > 0 and un > 0) else 0.0
    score = 0.6 * both + 0.4 * _band(per1k, 0.5, 4.0)
    return f"certain={hi} uncertain={un}", score


def m_triadic_load(ctx):
    """Tricolon and the not-just-X-but-Y frame, per 1000 words."""
    body = ctx["body"]
    tri = len(re.findall(r"\b[\w\-]+,\s+[\w\-]+,?\s+and\s+[\w\-]+\b", body))
    notjust = len(re.findall(
        r"\bnot\s+(?:just|only|merely|simply)\b[^.!?]{1,80}?\b(?:but|—|--)\b",
        body, re.I))
    isnt = len(re.findall(r"\bit'?s?\s+not\s+(?:about\s+)?\w+[,—-]\s*it'?s\b", body, re.I))
    per1k = (tri + notjust * 2 + isnt * 2) / max(len(ctx["words"]), 1) * 1000
    return per1k, 1.0 - _band(per1k, 1.5, 8.0)


def m_dash_density(ctx):
    body = ctx["body"]
    dashes = len(re.findall(r"—|\s--\s|\s–\s", body))
    per1k = dashes / max(len(ctx["words"]), 1) * 1000
    return per1k, 1.0 - _band(per1k, 2.0, 12.0)


def m_section_symmetry(ctx):
    """Uniform section lengths are a drafting-template signature."""
    raw = ctx["raw"]
    parts = re.split(r"^\s{0,3}#{1,6}\s+.*$", raw, flags=re.M)
    lengths = [len(words(p)) for p in parts if len(words(p)) > 20]
    if len(lengths) < 3:
        return None, None
    cv = _cv(lengths)
    return cv, _band(cv, 0.15, 0.55)


def m_contraction_rate(ctx):
    """Register breaks. Not about informality per se — about a consistent voice
    that occasionally relaxes, which templated prose does not do."""
    body = ctx["body"]
    contr = len(re.findall(r"\b\w+['’](?:s|t|re|ve|ll|d|m)\b", body))
    per100 = contr / max(len(ctx["words"]), 1) * 100
    return per100, _band(per100, 0.2, 2.5)


METRICS = [
    ("sentence_burstiness",  "Sentence-length variation (CV)",      m_sentence_burstiness,  1.6),
    ("paragraph_burstiness", "Paragraph-length variation (CV)",     m_paragraph_burstiness, 1.0),
    ("short_sentence_share", "Share of sentences <=7 words",        m_short_sentence_share, 1.0),
    ("signpost_density",     "Sentences opening with a connective", m_signpost_density,     1.4),
    ("opener_diversity",     "Sentence-opener entropy (norm.)",     m_opener_diversity,     1.0),
    ("specificity",          "Concrete referents / 100 words",      m_specificity,          1.8),
    ("abstraction_load",     "Abstract-register words / 100 words", m_abstraction_load,     1.2),
    ("hedge_density",        "Hedges / 100 words",                  m_hedge_density,        0.8),
    ("epistemic_range",      "Both certainty and open doubt",       m_epistemic_range,      1.4),
    ("triadic_load",         "Tricolon + not-just-X frames / 1k",   m_triadic_load,         1.0),
    ("dash_density",         "Em dashes / 1000 words",              m_dash_density,         0.6),
    ("section_symmetry",     "Section-length variation (CV)",       m_section_symmetry,     0.6),
    ("contraction_rate",     "Contractions / 100 words",            m_contraction_rate,     0.5),
]

# --------------------------------------------------------------------------
# Per-client weight profiles. Select with --profile NAME. Each maps a metric
# key to a weight that OVERRIDES the default above; unlisted keys keep their
# default weight. Build a profile from a --calibrate run: raise the axes that
# separate that client's approved human corpus from AI, cut the axes that don't.
#
# formal-technical: calibrated on 10 live client-published
# articles (human) vs 10 gpt-4o mirror drafts (ai). That formal, legal-checked
# voice carries its humanity in STRUCTURE and SPECIFICITY, not casual register,
# so the register axes (fragments, hedging, epistemic range, paragraph burst)
# are muted and section asymmetry / specificity / abstraction / tricolon lead.
# The corpus behind it was client content and is not distributed; build
# your own profile the same way with --calibrate.
# NOTE: dash_density kept at default despite a high calibrated separation — that
# separation was an artifact of gpt-4o emitting zero em dashes; the finding does
# not generalise, and §14 strips em dashes from output regardless.
# --------------------------------------------------------------------------

PROFILES = {
    "formal-technical": {
        "section_symmetry":     1.6,   # sep 1.76 — strongest discriminator
        "abstraction_load":     1.6,   # sep 1.63
        "specificity":          2.0,   # sep 1.34
        "triadic_load":         1.4,   # sep 1.15
        "sentence_burstiness":  1.4,   # sep 0.89
        "contraction_rate":     0.6,   # sep 0.96 (voice-sensitive; kept modest)
        "opener_diversity":     0.6,   # sep 0.63
        "hedge_density":        0.4,   # sep 0.64 (voice-sensitive)
        "signpost_density":     0.5,   # sep 0.05 — non-discriminating for this profile
        "paragraph_burstiness": 0.3,   # sep 0.16
        "short_sentence_share": 0.2,   # sep 0.15 — this formal voice avoids fragments
        "epistemic_range":      0.2,   # excluded from table + voice-sensitive for this profile
        # dash_density: unchanged (0.6) — see NOTE above.
    },
}


def apply_profile(name):
    """Rewrite the weight column of METRICS from a named profile."""
    prof = PROFILES.get(name)
    if prof is None:
        raise SystemExit(
            f"unknown profile '{name}'; known profiles: "
            f"{', '.join(sorted(PROFILES)) or '(none)'}")
    global METRICS
    METRICS = [(k, label, fn, prof.get(k, w)) for (k, label, fn, w) in METRICS]


def analyse(raw):
    body = prose_body(raw)
    ctx = {
        "raw": raw,
        "body": body,
        "paras": paragraphs(body),
        "sents": sentences(body),
        "words": words(body),
    }
    results = {}
    weighted, total_w = 0.0, 0.0
    for key, label, fn, weight in METRICS:
        value, score = fn(ctx)
        if score is None:
            results[key] = {"label": label, "value": None, "score": None,
                            "note": "not applicable"}
            continue
        results[key] = {"label": label, "value": value, "score": round(score, 3)}
        weighted += score * weight
        total_w += weight
    composite = weighted / total_w if total_w else 0.0
    return {
        "word_count": len(ctx["words"]),
        "sentence_count": len(ctx["sents"]),
        "paragraph_count": len(ctx["paras"]),
        "composite": round(composite, 3),
        "metrics": results,
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def bar(score, width=18):
    filled = int(round(score * width))
    return "#" * filled + "." * (width - filled)


def fmt_value(v):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def report(res, path):
    lines = []
    lines.append(f"\n  {path}")
    lines.append(f"  {res['word_count']} words / {res['sentence_count']} sentences "
                 f"/ {res['paragraph_count']} paragraphs")
    lines.append("")
    weak = []
    for key, label, _fn, _w in METRICS:
        m = res["metrics"][key]
        if m["score"] is None:
            continue
        s = m["score"]
        marker = " " if s >= 0.5 else ("!" if s >= 0.25 else "!!")
        lines.append(f"  {marker:<2} {label:<38} {fmt_value(m['value']):>8}  "
                     f"{bar(s)} {s:.2f}")
        if s < 0.4:
            weak.append((s, label, key))
    lines.append("")
    lines.append(f"  COMPOSITE  {bar(res['composite'], 30)}  {res['composite']:.2f}")
    if weak:
        weak.sort()
        lines.append("")
        lines.append("  Weakest axes — fix these first:")
        for s, label, key in weak[:4]:
            lines.append(f"    - {label} ({s:.2f})  -> {REMEDY.get(key, '')}")
    lines.append("")
    return "\n".join(lines)


REMEDY = {
    "sentence_burstiness":
        "split one long sentence into a long one and a very short one; don't average",
    "paragraph_burstiness":
        "let one paragraph run long and cut another to a single line",
    "short_sentence_share":
        "add 2-3 sentences under 7 words at points of emphasis",
    "signpost_density":
        "delete the connective and let the juxtaposition carry it",
    "opener_diversity":
        "too many sentences start the same way; recast openings",
    "specificity":
        "name the REAL client, number, date, tool; do not invent one to game this axis",
    "abstraction_load":
        "swap abstract nouns for the concrete thing they stand in for",
    "hedge_density":
        "commit to a claim somewhere; not everything can be 'often' and 'typically'",
    "epistemic_range":
        "state one thing flatly and admit one thing you don't know",
    "triadic_load":
        "break up the lists of three; use two items or four",
    "dash_density":
        "convert some em dashes to full stops or commas",
    "section_symmetry":
        "let attention be asymmetric — one section should be much longer",
    "contraction_rate":
        "allow the register to relax in places",
}


# --------------------------------------------------------------------------
# Calibration
# --------------------------------------------------------------------------

def read_dir(d):
    out = []
    for root, _dirs, files in os.walk(d):
        for f in sorted(files):
            if f.startswith("."):
                continue
            if os.path.splitext(f)[1].lower() not in (".md", ".txt", ".markdown"):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            if len(words(text)) >= 150:
                out.append((p, text))
    return out


def calibrate(human_dir, ai_dir):
    sets = {"human": read_dir(human_dir), "ai": read_dir(ai_dir)}
    for name, docs in sets.items():
        if not docs:
            print(f"no usable documents (>=150 words) found in {name} directory",
                  file=sys.stderr)
            return 1

    stats = {name: {} for name in sets}
    for name, docs in sets.items():
        per_metric = {k: [] for k, _l, _f, _w in METRICS}
        comps = []
        for _p, text in docs:
            r = analyse(text)
            comps.append(r["composite"])
            for k, _l, _f, _w in METRICS:
                v = r["metrics"][k]["value"]
                if isinstance(v, (int, float)):
                    per_metric[k].append(v)
        stats[name]["composite"] = comps
        stats[name]["metrics"] = per_metric

    print(f"\n  calibration: {len(sets['human'])} human docs vs "
          f"{len(sets['ai'])} AI docs\n")
    print(f"  {'metric':<38} {'human med':>10} {'ai med':>10} {'sep':>7}")
    print("  " + "-" * 68)
    for k, label, _f, _w in METRICS:
        h = stats["human"]["metrics"][k]
        a = stats["ai"]["metrics"][k]
        if len(h) < 2 or len(a) < 2:
            continue
        hm, am = statistics.median(h), statistics.median(a)
        pooled = statistics.pstdev(h + a)
        sep = abs(hm - am) / pooled if pooled else 0.0
        star = " *" if sep >= 0.8 else ""
        print(f"  {label:<38} {hm:>10.2f} {am:>10.2f} {sep:>7.2f}{star}")
    hc = statistics.median(stats["human"]["composite"])
    ac = statistics.median(stats["ai"]["composite"])
    print("  " + "-" * 68)
    print(f"  {'COMPOSITE':<38} {hc:>10.2f} {ac:>10.2f}")
    print("\n  '*' marks axes that separate your two corpora well (>=0.8 pooled SD).")
    print("  Axes with low separation are not discriminating for your content —")
    print("  drop their weight in METRICS rather than chasing them.\n")
    print("  Set your review threshold between the two composite medians,")
    print(f"  i.e. around {(hc + ac) / 2:.2f} for this corpus.\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files to score, or - for stdin")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--calibrate", nargs=2, metavar=("HUMAN_DIR", "AI_DIR"),
                    help="compare two reference corpora and report axis separation")
    ap.add_argument("--threshold", type=float, default=None,
                    help="exit 1 if any composite falls below this value")
    ap.add_argument("--profile", default=None,
                    help=f"apply a per-client weight profile: "
                         f"{', '.join(sorted(PROFILES)) or '(none defined)'}")
    args = ap.parse_args()

    if args.profile:
        apply_profile(args.profile)

    if args.calibrate:
        return calibrate(*args.calibrate)

    if not args.paths:
        ap.print_help()
        return 2

    out, worst = [], 1.0
    for path in args.paths:
        if path == "-":
            raw, name = sys.stdin.read(), "<stdin>"
        else:
            with open(path, encoding="utf-8") as fh:
                raw = fh.read()
            name = path
        if len(words(prose_body(raw))) < 100:
            print(f"{name}: under 100 words of prose, scores unreliable",
                  file=sys.stderr)
        res = analyse(raw)
        res["path"] = name
        worst = min(worst, res["composite"])
        out.append(res)

    if args.json:
        print(json.dumps(out if len(out) > 1 else out[0], indent=2))
    else:
        for res in out:
            print(report(res, res["path"]))

    if args.threshold is not None and worst < args.threshold:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # piped into head/less; suppress the interpreter's shutdown warning
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
