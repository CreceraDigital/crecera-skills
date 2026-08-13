"""Render the analyzer output as a Keyword Guidelines .txt and a structured .json.

The .txt format mirrors Surfer's content-editor export exactly so it can be
pasted into any tool that already consumes Surfer guidelines.

Usage:
    python render.py \
        --analysis _work/analysis.json \
        --facts _work/facts.md \
        --keyword "deskless workers" \
        --out-txt "out/Keyword Guidelines [deskless workers].txt" \
        --out-json "out/Keyword Guidelines [deskless workers].json"
"""
import argparse
import json
import re
from pathlib import Path


def fmt_range(lo, hi):
    """Format a min-max range, preserving 'Infinity' as a literal string."""
    if hi == "Infinity":
        return f"{lo} - Infinity"
    return f"{lo} - {hi}"


def render_txt(analysis, facts_md):
    s = analysis["structure"]
    lines = []

    # CONTENT STRUCTURE
    lines.append("## CONTENT STRUCTURE")
    lines.append(f"* Characters: {fmt_range(s['characters']['min'], s['characters']['max'])}")
    lines.append(f"* Images: {fmt_range(s['images']['min'], s['images']['max'])}")
    lines.append(f"* Headings: {fmt_range(s['headings']['min'], s['headings']['max'])}")
    lines.append(f"* Paragraphs: {fmt_range(s['paragraphs']['min'], s['paragraphs']['max'])}")
    lines.append(f"* Words: {fmt_range(s['words']['min'], s['words']['max'])}")
    lines.append("")

    # IMPORTANT TERMS TO USE
    lines.append("## IMPORTANT TERMS TO USE")
    lines.append("_Make sure to include those as many times as stated._")
    for t in analysis["terms"]:
        lines.append(f"* {t['term']}: {t['min_per_page']} - {t['max_per_page']}")
    lines.append("")

    # QUESTIONS TO ANSWER
    lines.append("## QUESTIONS TO ANSWER")
    for q in analysis["questions"]:
        lines.append(f"* {q}")
    lines.append("")

    # TOPICS TO COVER (mirrors Surfer's Topics & Questions panel — competitor H1/H2/H3 + PAA, deduped)
    topics = analysis.get("topics", [])
    if topics:
        lines.append("## TOPICS TO COVER")
        lines.append("_Drawn from competitor headings and People Also Ask. Pick the ones relevant to your angle._")
        # Group: PAA first, then competitors. Within each, the analyzer already ordered by page_count.
        paa = [t for t in topics if t["source"] == "people_also_ask"]
        comp = [t for t in topics if t["source"] == "competitors"]
        if paa:
            lines.append("")
            lines.append("### From People Also Ask")
            for t in paa:
                lines.append(f"* {t['text']}")
        if comp:
            lines.append("")
            lines.append("### From competitor headings")
            for t in comp:
                count_tag = f" ({t['page_count']}×)" if t["page_count"] > 1 else ""
                lines.append(f"* {t['text']}{count_tag}")
        lines.append("")

    # FACTS TO INCLUDE
    lines.append("## FACTS TO INCLUDE")
    lines.append("_Facts are grouped by topics._")
    facts_md = (facts_md or "").strip()
    if facts_md:
        # Trust the LLM output format: ### Heading then * bullets
        lines.append(facts_md)
    else:
        lines.append("_No facts extracted (no source content was substantial enough)._")
    lines.append("")

    return "\n".join(lines)


def parse_facts_md(facts_md):
    """Convert the LLM facts markdown into structured clusters."""
    if not facts_md:
        return []
    clusters = []
    current = None
    for raw in facts_md.splitlines():
        line = raw.rstrip()
        if line.startswith("### "):
            if current:
                clusters.append(current)
            current = {"topic": line[4:].strip(), "facts": []}
        elif line.startswith("* ") and current is not None:
            current["facts"].append(line[2:].strip())
    if current:
        clusters.append(current)
    return clusters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--facts", required=False, default="", help="Path to LLM-extracted facts markdown")
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    analysis = json.loads(Path(args.analysis).read_text(encoding="utf-8"))
    facts_md = Path(args.facts).read_text(encoding="utf-8") if args.facts and Path(args.facts).exists() else ""

    # .txt
    txt = render_txt(analysis, facts_md)
    Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_txt).write_text(txt, encoding="utf-8")

    # .json
    out_json = {
        "keyword": args.keyword,
        "pages_analyzed": analysis["pages_analyzed"],
        "structure": analysis["structure"],
        "terms": analysis["terms"],
        "questions": analysis["questions"],
        "topics": analysis.get("topics", []),
        "fact_clusters": parse_facts_md(facts_md),
        "per_page_stats": analysis.get("per_page_stats", []),
    }
    Path(args.out_json).write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    print(f"Wrote {args.out_txt}")
    print(f"Wrote {args.out_json}")


if __name__ == "__main__":
    main()
