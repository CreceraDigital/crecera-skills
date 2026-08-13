#!/usr/bin/env python3
"""
surfer-keyword-tester: score an article against a pasted Surfer Important Terms
list, then rank which terms to add for maximum score lift.

Usage:
    python score.py --article article.txt --terms terms.txt --out report.json [--target-score 80]

The score is a *term-compliance* score (0-100), not Surfer's full score. It
tracks Surfer's direction-of-change faithfully for keyword-only edits because
the user's keyword-test loop only changes term frequencies, never structural
signals (word count, headings, paragraphs, images).
"""

import argparse
import json
import re
import sys
from pathlib import Path


TERM_LINE_RE = re.compile(
    r"""^\s*
        (?:[*\-•·]\s+)?            # optional bullet
        (?P<term>.+?)                          # term (lazy)
        \s*[:|\t]\s*                           # explicit separator: colon, pipe, or tab
        (?P<min>\d+)
        \s*(?:-|–|—|to)\s*           # range separator
        (?P<max>\d+)
        \s*$""",
    re.VERBOSE | re.IGNORECASE,
)

# Fallback: "term   33-57" or "term 33 - 57" with whitespace separator
TERM_LINE_WS_RE = re.compile(
    r"""^\s*
        (?:[*\-•·]\s+)?
        (?P<term>.+?)
        \s+
        (?P<min>\d+)
        \s*(?:-|–|—|to)\s*
        (?P<max>\d+)
        \s*$""",
    re.VERBOSE | re.IGNORECASE,
)


def parse_terms(text: str) -> list[dict]:
    """Parse a Surfer Important Terms paste into [{term, min, max}, ...]."""
    terms = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        # Skip the Surfer header lines users often paste alongside the list
        low = line.lower()
        if low.startswith("important terms") or low.startswith("make sure to include"):
            continue
        m = TERM_LINE_RE.match(line) or TERM_LINE_WS_RE.match(line)
        if not m:
            continue
        term = m.group("term").strip().rstrip(":").strip()
        # Trim trailing parenthetical hints like "(used 3 times)"
        term = re.sub(r"\s*\([^)]*\)\s*$", "", term).strip()
        if not term or term.lower() in seen:
            continue
        seen.add(term.lower())
        terms.append({
            "term": term,
            "min": int(m.group("min")),
            "max": int(m.group("max")),
        })
    return terms


def count_term(article_text: str, term: str) -> int:
    """Case-insensitive, whole-phrase, word-boundary-anchored occurrence count."""
    pattern = re.compile(
        r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    return len(pattern.findall(article_text))


def compliance(count: int, lo: int, hi: int) -> float:
    """Per-term compliance, 0.0 to 1.0."""
    if lo <= 0:
        lo = 1
    if count == 0:
        return 0.0
    if lo <= count <= hi:
        return 1.0
    if count < lo:
        return count / lo
    overshoot = count - hi
    return max(0.0, 1.0 - overshoot / max(hi, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", required=True)
    ap.add_argument("--terms", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-score", type=float, default=80.0)
    args = ap.parse_args()

    article = Path(args.article).read_text(encoding="utf-8")
    terms_text = Path(args.terms).read_text(encoding="utf-8")

    terms = parse_terms(terms_text)
    if not terms:
        print("ERROR: could not parse any terms. Check the input format.", file=sys.stderr)
        print("Expected lines like:  deskless workers: 33 - 57", file=sys.stderr)
        sys.exit(1)

    n_terms = len(terms)
    rows = []
    for t in terms:
        count = count_term(article, t["term"])
        c = compliance(count, t["min"], t["max"])
        row = {
            "term": t["term"],
            "min": t["min"],
            "max": t["max"],
            "current": count,
            "compliance": round(c, 3),
            "additions_needed": max(0, t["min"] - count),
            "excess": max(0, count - t["max"]),
        }
        if count == 0 or count < t["min"]:
            row["status"] = "gap"
        elif count > t["max"]:
            row["status"] = "over"
        else:
            row["status"] = "compliant"
        rows.append(row)

    baseline_score = sum(r["compliance"] for r in rows) / n_terms * 100

    # For each gap term, lift = (1 - current_compliance) / n_terms * 100
    # (i.e., bringing this term to min gives it compliance=1, contributing 1/n_terms to the mean)
    for r in rows:
        if r["status"] == "gap":
            r["lift"] = round((1.0 - r["compliance"]) / n_terms * 100, 2)
        else:
            r["lift"] = 0.0

    gap_terms = sorted(
        [r for r in rows if r["status"] == "gap" and r["lift"] > 0],
        key=lambda x: x["lift"],
        reverse=True,
    )
    compliant_terms = [r for r in rows if r["status"] == "compliant"]
    over_terms = sorted(
        [r for r in rows if r["status"] == "over"],
        key=lambda x: x["excess"],
        reverse=True,
    )

    projected = baseline_score + sum(r["lift"] for r in gap_terms)

    report = {
        "baseline_score": round(baseline_score, 1),
        "projected_score_if_all_applied": round(projected, 1),
        "target_score": args.target_score,
        "reaches_target": projected >= args.target_score,
        "n_terms": n_terms,
        "n_gap": len(gap_terms),
        "n_compliant": len(compliant_terms),
        "n_over": len(over_terms),
        "gap_terms": gap_terms,
        "compliant_terms": compliant_terms,
        "over_terms": over_terms,
    }

    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Baseline term-compliance score: {baseline_score:.1f}/100")
    print(f"Projected after applying all gap terms: {projected:.1f}/100  "
          f"(target {args.target_score:.0f})")
    print(f"Gap: {len(gap_terms)}  |  Compliant: {len(compliant_terms)}  |  Over: {len(over_terms)}")


if __name__ == "__main__":
    main()
