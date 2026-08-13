"""Surfer-brief analyzer.

Reads parsed competitor pages (one JSON per page) plus the SERP response,
and emits a single analysis.json with:

  - structure ranges (chars/words/headings/paragraphs/images, min..max across pages)
  - term frequency ranges for 1-3 grams (min..max occurrences across pages that contain the term)
  - question candidates (from SERP PAA + competitor H2/H3)
  - per-page raw stats (for the render step)

Each input page JSON should look like:

    {
      "url": "https://...",
      "text": "...",                # body text, plain (REQUIRED)
      "html": "...",                # raw HTML (optional, used to recompute structure if present)
      "headings": ["...", "..."],   # optional, pre-extracted heading texts
      "image_count": 12             # optional
    }

If `html` is present we re-parse it to get accurate structure counts.
If only `text` is present, headings/images/paragraphs default to whatever was supplied (or 0).

Usage:
    python analyze.py --pages _work/pages --serp _work/serp.json --keyword "deskless workers" --out _work/analysis.json
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


STOP_WORDS = {
    # articles, pronouns, prepositions, copulas
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to", "in",
    "on", "at", "by", "for", "with", "as", "is", "are", "was", "were", "be",
    "been", "being", "am", "do", "does", "did", "doing", "have", "has", "had",
    "having", "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
    "our", "their", "mine", "yours", "ours", "theirs", "what", "which", "who",
    "whom", "whose", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "should", "now", "from", "up", "down", "out", "off", "over", "under",
    "again", "further", "once", "here", "there", "about", "into", "through",
    "during", "before", "after", "above", "below", "between", "against", "while",
    "because", "until", "since",
    # numbers / time generic
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "first", "second", "third", "year", "years", "month", "months",
    "week", "day", "days", "today", "tomorrow", "yesterday",
    # common SEO/UX boilerplate
    "read", "more", "learn", "click", "here", "see", "view", "find",
    "discover", "explore", "check", "back", "next", "previous", "page",
    "home", "menu", "toggle", "skip", "search", "sign", "login", "logout",
    "register", "subscribe", "follow", "share", "like", "comment", "post",
    "article", "blog", "category", "tag", "author", "published", "updated",
    "copyright", "rights", "reserved", "privacy", "policy", "terms", "cookie",
    "cookies",
    # weak / generic verbs and adverbs that pollute term lists
    "may", "might", "must", "would", "could", "shall", "ought",
    "make", "makes", "made", "making",
    "get", "gets", "got", "getting", "gotten",
    "go", "goes", "going", "gone", "went",
    "come", "comes", "coming", "came", "become", "becomes", "becoming",
    "want", "wants", "wanted", "wanting",
    "know", "knows", "knowing", "knew", "known",
    "think", "thinks", "thinking", "thought",
    "say", "says", "said", "saying",
    "give", "gives", "given", "gave", "giving",
    "take", "takes", "took", "taken", "taking",
    "include", "includes", "included", "including",
    "need", "needs", "needed", "needing",
    "help", "helps", "helped", "helping",
    "use", "uses", "used", "using",
    "also", "however", "therefore", "thus", "hence", "moreover", "furthermore",
    "often", "sometimes", "usually", "always", "never", "rarely", "seldom",
    "really", "actually", "literally", "basically", "essentially", "generally",
    "specifically", "particularly",
    "even", "still", "yet", "already", "even",
    "well", "best", "better", "worse", "worst",
    "good", "great", "bad",
    "much", "less", "lot", "lots",
    "way", "ways",
    "many", "every",
    "thing", "things", "stuff",
    "new", "old",
    "due",
    "across",
    "though", "although",
    "without", "within",
    "around",
    "able",
    "various",
    "different",
    "important",
    "example", "examples",
    "let", "lets", "letting",
    "look", "looks", "looking", "looked",
    "people", "person", "everyone", "someone", "anyone",
    "today", "currently", "recently",
    "thats", "its", "youre", "theyre", "weve", "youve",  # contractions stripped of apostrophes
    "don't", "don", "doesn", "doesnt", "didn", "didnt", "isn", "isnt",
    "aren", "arent", "wasn", "wasnt", "weren", "werent",
    "wouldn", "wouldnt", "couldn", "couldnt", "shouldn", "shouldnt",
}

GENERIC_BIGRAM_BLOCKLIST = {
    "read more", "learn more", "click here", "find out", "sign up", "log in",
    "privacy policy", "terms conditions", "all rights", "rights reserved",
    "main content", "skip main", "table contents",
}


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def load_pages(pages_dir):
    """Return list of page dicts. Each must include url + text at minimum."""
    pages = []
    for p in sorted(Path(pages_dir).glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {p.name}: {e}", file=sys.stderr)
            continue
        if not data.get("text") and not data.get("html") and not data.get("markdown"):
            print(f"  skip {p.name}: no text, html, or markdown", file=sys.stderr)
            continue
        pages.append(data)
    return pages


def parse_html_structure(html):
    """Given raw HTML, return text + structural counts.

    Strips nav/header/footer/aside/script/style before counting.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["nav", "header", "footer", "aside", "script", "style", "noscript", "form"]):
        tag.decompose()
    main = (soup.find("main") or soup.find("article") or
            soup.find(attrs={"role": "main"}) or soup.find("body") or soup)
    headings = [h.get_text(strip=True) for h in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]) if h.get_text(strip=True)]
    paragraphs = [p.get_text(strip=True) for p in main.find_all("p") if p.get_text(strip=True)]
    images = main.find_all("img")
    text = main.get_text(separator=" ", strip=True)
    return {
        "text": text,
        "headings": headings,
        "paragraph_count": len(paragraphs),
        "image_count": len(images),
        "heading_count": len(headings),
    }


def parse_markdown_structure(md):
    """Extract structure from markdown text (DataforSEO content parser output)."""
    headings = []
    paragraphs = 0
    # Strip code fences before counting structure
    lines = md.split("\n")
    in_code = False
    text_lines = []
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            heading_text = m.group(2).strip()
            # strip markdown link syntax in heading
            heading_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading_text)
            if heading_text:
                headings.append(heading_text)
        text_lines.append(line)
    # Paragraph count: blocks of non-heading, non-blank text separated by blank lines
    blocks = re.split(r"\n\s*\n", md)
    paragraphs = sum(
        1 for b in blocks
        if b.strip() and not b.strip().startswith("#") and not b.strip().startswith("|")
    )
    image_count = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", md))
    # Body text: strip markdown link syntax, headings, and code fences for cleaner term counting
    body = re.sub(r"```.*?```", " ", md, flags=re.DOTALL)
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)  # links → anchor text
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", body)  # images out
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)
    body = re.sub(r"[*_`>]+", " ", body)
    return {
        "text": body,
        "headings": headings,
        "heading_count": len(headings),
        "paragraph_count": paragraphs,
        "image_count": image_count,
    }


def page_structure(page):
    """Extract structural counts for a single page, preferring HTML, then markdown, then raw."""
    if page.get("html"):
        parsed = parse_html_structure(page["html"])
        if parsed:
            return parsed
    if page.get("markdown"):
        return parse_markdown_structure(page["markdown"])
    # Fallback: derive from provided fields
    text = page.get("text", "")
    headings = page.get("headings") or []
    return {
        "text": text,
        "headings": headings,
        "heading_count": len(headings),
        "paragraph_count": page.get("paragraph_count", text.count("\n\n") + 1 if text else 0),
        "image_count": page.get("image_count", 0),
    }


WORD_RE = re.compile(r"[a-z][a-z'\-]+")


def tokenize(text):
    return WORD_RE.findall(text.lower())


def ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def is_valid_term(term):
    """Decide whether an n-gram is keep-worthy.

    Unigrams: token must not be a stop word and must be ≥ 2 chars.
    Multi-grams: only the *boundary* tokens (first and last) must be content words.
    Interior tokens may be stop words ("transportation and manufacturing industries",
    "lack of employee engagement"). This matches Surfer's phrase shapes and is the
    biggest single improvement over naive "every token must be a content word".
    """
    parts = term.split()
    if not parts:
        return False
    # blocklist of explicit garbage phrases
    if term in GENERIC_BIGRAM_BLOCKLIST:
        return False
    # every token has to clear the minimum length
    for t in parts:
        if len(t) < 2:
            return False
    if len(parts) == 1:
        return parts[0] not in STOP_WORDS
    # multi-gram: only first and last tokens must be content words
    if parts[0] in STOP_WORDS or parts[-1] in STOP_WORDS:
        return False
    # but at least one *content* word in the interior helps too — if all interior
    # tokens are stop words AND the phrase is 3+ tokens, the phrase is probably
    # something like "lack of feedback" (good) or "way to the" (bad). Require ≥ 50%
    # non-stop tokens.
    non_stop = sum(1 for t in parts if t not in STOP_WORDS)
    if non_stop < (len(parts) + 1) // 2:
        return False
    return True


def page_term_counts(text, n_range=(1, 5)):
    """Return {term: count} for valid n-grams on one page.

    Default n-gram range is 1-5 (Surfer extracts up to 5-word phrases like
    "transportation and manufacturing industries").
    """
    tokens = tokenize(text)
    counts = Counter()
    for n in range(n_range[0], n_range[1] + 1):
        for g in ngrams(tokens, n):
            if is_valid_term(g):
                counts[g] += 1
    return counts


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def range_with_infinity(values, infinity_threshold_multiplier=2.0):
    """Return (min, max_or_infinity) tuple. Mirrors Surfer's 'N - Infinity' behavior
    when max greatly exceeds the median (heuristic: max > 2x median)."""
    if not values:
        return (0, 0)
    lo = min(values)
    hi = max(values)
    med = median(values)
    if med > 0 and hi > med * infinity_threshold_multiplier:
        return (lo, "Infinity")
    return (lo, hi)


def _trim_range(values, trim_threshold=8):
    """Return (min, max) for the range, trimming one outlier from each end when N >= trim_threshold.

    For small samples (N < threshold) returns plain min/max. For N >= threshold we drop
    the single lowest and single highest before taking the bounds — this prevents one thin
    product page or one outlier deep-dive from blowing the range out.
    """
    if not values:
        return (0, 0)
    if len(values) >= trim_threshold:
        trimmed = sorted(values)[1:-1]
        return (min(trimmed), max(trimmed))
    return (min(values), max(values))


def compute_structure(page_stats):
    """Compute Surfer-style structure ranges from per-page stats.

    For samples of 8+ pages, drops the lowest and highest before computing min/max
    (matches Surfer's apparent percentile-trim behavior). For smaller samples uses raw bounds.
    """
    chars = [s["char_count"] for s in page_stats]
    words = [s["word_count"] for s in page_stats]
    headings = [s["heading_count"] for s in page_stats]
    paragraphs = [s["paragraph_count"] for s in page_stats]
    images = [s["image_count"] for s in page_stats]

    chars_lo, chars_hi = _trim_range(chars)
    words_lo, words_hi = _trim_range(words)
    headings_lo, headings_hi = _trim_range(headings)
    images_lo, images_hi = _trim_range(images)
    paragraphs_lo, _ = _trim_range(paragraphs)

    return {
        "characters": {"min": chars_lo, "max": chars_hi},
        "words": {"min": words_lo, "max": words_hi},
        "headings": {"min": headings_lo, "max": headings_hi},
        # paragraphs still gets the Infinity treatment over the full sample (matches Surfer)
        "paragraphs": {"min": paragraphs_lo, "max": range_with_infinity(paragraphs)[1]},
        "images": {"min": images_lo, "max": images_hi},
    }


def compute_terms(per_page_counts, min_pages=3, max_terms=300):
    """Aggregate per-page term counts into Surfer-style ranges.

    A term qualifies if it appears in `min_pages` or more pages.
    The range for a term is the min..max occurrence count across pages that contain it.

    Default max_terms is 300 — Surfer typically exposes 200-400 terms; capping at 120
    (the old default) cut off the long tail that documents are actually scored against.
    """
    # term -> list of counts (only from pages that have it)
    term_to_counts = defaultdict(list)
    for counts in per_page_counts:
        for term, c in counts.items():
            term_to_counts[term].append(c)

    qualified = []
    for term, counts in term_to_counts.items():
        if len(counts) < min_pages:
            continue
        # filter: drop terms where max count is just 1 (not really "used") unless on many pages
        if max(counts) < 2 and len(counts) < 5:
            continue
        qualified.append({
            "term": term,
            "pages_with_term": len(counts),
            "min_per_page": min(counts),
            "max_per_page": max(counts),
            "total_occurrences": sum(counts),
        })

    # Rank: pages first (broader use is more salient), then total occurrences,
    # then phrase length (prefer longer phrases when other factors tie — they're more specific).
    qualified.sort(
        key=lambda x: (x["pages_with_term"], x["total_occurrences"], len(x["term"].split())),
        reverse=True,
    )

    # Dedup near-overlaps: prefer longer phrase when shorter is just its prefix/suffix and counts close
    qualified = _dedupe_overlapping_terms(qualified)

    return qualified[:max_terms]


def _dedupe_overlapping_terms(terms):
    """Drop a unigram when a containing multi-gram explains nearly all of its uses.

    Surfer keeps both `communication strategy` and `internal communication strategy` —
    they're scored separately. So we only dedup unigrams (single words) against
    multi-grams that contain them, and only when the multi-gram covers ≥ 85% of the
    unigram's uses (the unigram adds no extra signal).

    This is intentionally less aggressive than the previous logic: writers benefit
    from seeing both `communication strategy` AND `internal communication strategy`
    in the brief, because Surfer scores against both.
    """
    by_term = {t["term"]: t for t in terms}
    keep = set(by_term.keys())
    for t in terms:
        parts = t["term"].split()
        if len(parts) < 2:
            continue
        # Only drop unigrams (single-word sub-phrases) that are tokens of this multi-gram
        for sub in parts:
            if sub in by_term and sub in keep:
                sub_count = by_term[sub]["total_occurrences"]
                multi_count = t["total_occurrences"]
                # Drop the unigram only if the longer phrase covers ≥ 85% of its uses
                if multi_count >= sub_count * 0.85:
                    keep.discard(sub)
    return [t for t in terms if t["term"] in keep]


def extract_questions(serp_data, page_stats, max_questions=10):
    """Pull questions from SERP people_also_ask + competitor H2/H3 matching question shape.

    Questions are a subset of topics: those phrased as direct questions. The full
    competitor heading set is captured separately by extract_topics().
    """
    questions = []
    seen = set()

    def add(q):
        q_clean = q.strip()
        key = re.sub(r"[\?\.\,\;\:\!]+\s*$", "", q_clean).lower()
        if not key or key in seen or len(q_clean) < 8:
            return
        seen.add(key)
        # Only append ? if the string has no question mark at all
        if "?" not in q_clean:
            q_clean += "?"
        questions.append(q_clean)

    # SERP PAA
    serp_results = _walk_for_paa(serp_data)
    for paa_text in serp_results:
        add(paa_text)

    # Headings from competitors that look like questions
    q_re = re.compile(r"^(what|how|why|when|where|is|are|can|do|does|should|which|who)\b", re.IGNORECASE)
    for ps in page_stats:
        for h in ps.get("headings", []):
            if q_re.match(h.strip()):
                add(h)

    return questions[:max_questions]


# Headings that almost always indicate non-content sections — skip when surfacing topics.
TOPIC_BLOCKLIST_PATTERNS = [
    r"^(related|recent|popular|trending|featured|latest)\s+(posts?|articles?|reads?|content|stories)",
    r"^(other\s+)?posts? you might (be interested in|like|enjoy)",
    r"^about (the|our) (author|team|company)",
    r"^author\s+bio",
    r"^share (this|article|post)",
    r"^(sign up|subscribe|join (our|the) newsletter|newsletter sign-?up)",
    r"^(get started|try (it|us) (free|for free)|book a demo|request a demo|free trial)",
    r"^(contact|reach) us",
    r"^get in touch",
    r"^(comments?|leave a (comment|reply))",
    r"^(categor(ies|y)|tags?|archives?)",
    r"^(table of contents|toc|in this article|on this page)",
    r"^(the )?bottom line$",
    r"^(in )?conclusion$",
    r"^(key takeaways?|summary|tldr|tl;dr)$",
    r"^references?$",
    r"^footnotes?$",
    r"^citations?$",
    r"^keep up with",
    r"^continue reading",
    r"^read (next|also|more)",
    r"^you might (also )?like",
    r"^download (the|our|now)",
    r"^watch (the )?(video|webinar)",
    r"^(privacy|cookie|terms)",
]
TOPIC_BLOCKLIST_RE = re.compile("|".join(TOPIC_BLOCKLIST_PATTERNS), re.IGNORECASE)


def _normalize_topic(text):
    """Lowercase, strip punctuation, collapse whitespace — for dedupe keying."""
    t = text.lower().strip()
    t = re.sub(r"[\.\,\:\;\!\?\(\)\[\]\"'`]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def extract_topics(serp_data, page_stats, max_topics=80):
    """Collect all competitor headings + PAA into a deduped, source-tagged topic list.

    Mirrors Surfer's Topics & Questions panel:
      - PAA items become topics with source="people_also_ask"
      - All competitor H1/H2/H3 (filtered for boilerplate) become source="competitors"
      - Near-duplicates collapse and increment a count

    Sorted by (source priority, page_count desc, length asc-ish).
    """
    topics_by_key = {}

    def add(text, source):
        text = text.strip()
        if not text or len(text) < 6 or len(text) > 200:
            return
        if TOPIC_BLOCKLIST_RE.search(text):
            return
        # collapse all-caps boilerplate, single-word, etc.
        if len(text.split()) < 2:
            return
        key = _normalize_topic(text)
        if not key:
            return
        if key in topics_by_key:
            entry = topics_by_key[key]
            entry["page_count"] += 1
            # prefer the longer / more descriptive surface form
            if len(text) > len(entry["text"]):
                entry["text"] = text
        else:
            topics_by_key[key] = {"text": text, "source": source, "page_count": 1}

    # PAA
    for paa_text in _walk_for_paa(serp_data):
        add(paa_text, "people_also_ask")

    # Competitor headings (only H1-H3 are reliably topical; H4+ tends to be sub-points)
    for ps in page_stats:
        for h in ps.get("headings", []):
            add(h, "competitors")

    topics = list(topics_by_key.values())
    # PAA first (matches Surfer's ordering), then competitor topics by page_count desc
    source_order = {"people_also_ask": 0, "competitors": 1}
    topics.sort(key=lambda t: (source_order.get(t["source"], 2), -t["page_count"], len(t["text"])))
    return topics[:max_topics]


def _walk_for_paa(obj):
    """Recursively walk SERP JSON looking for people_also_ask question strings."""
    out = []
    if isinstance(obj, dict):
        if obj.get("type") in ("people_also_ask_element", "people_also_ask"):
            for key in ("title", "question", "expanded_element"):
                v = obj.get(key)
                if isinstance(v, str):
                    out.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            t = item.get("title") or item.get("question")
                            if isinstance(t, str):
                                out.append(t)
        for v in obj.values():
            out.extend(_walk_for_paa(v))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_walk_for_paa(item))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", required=True, help="Directory containing per-page JSON files")
    parser.add_argument("--serp", required=True, help="SERP response JSON path")
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--image-counts", help="Optional JSON of {url: image_count} (from count_images.py)")
    parser.add_argument("--min-pages-per-term", type=int, default=3)
    parser.add_argument("--max-terms", type=int, default=300)
    args = parser.parse_args()

    pages = load_pages(args.pages)
    if len(pages) < 5:
        print(f"ERROR: only {len(pages)} usable pages — need >=5 to compute meaningful ranges.", file=sys.stderr)
        sys.exit(1)

    image_counts_by_url = {}
    if args.image_counts and Path(args.image_counts).exists():
        raw = json.loads(Path(args.image_counts).read_text(encoding="utf-8"))
        image_counts_by_url = {u: c for u, c in raw.items() if isinstance(c, int)}

    page_stats = []
    per_page_counts = []
    for p in pages:
        struct = page_structure(p)
        text = struct["text"]
        word_count = len(text.split())
        url = p.get("url", "")
        # Prefer explicit image count from count_images.py over markdown-derived count
        image_count = image_counts_by_url.get(url, struct["image_count"])
        page_stats.append({
            "url": url,
            "char_count": len(text),
            "word_count": word_count,
            "heading_count": struct["heading_count"],
            "paragraph_count": struct["paragraph_count"],
            "image_count": image_count,
            "headings": struct["headings"],
        })
        per_page_counts.append(page_term_counts(text))

    # SERP for PAA
    serp_data = json.loads(Path(args.serp).read_text(encoding="utf-8"))

    analysis = {
        "keyword": args.keyword,
        "pages_analyzed": len(pages),
        "structure": compute_structure(page_stats),
        "terms": compute_terms(per_page_counts, min_pages=args.min_pages_per_term, max_terms=args.max_terms),
        "questions": extract_questions(serp_data, page_stats),
        "topics": extract_topics(serp_data, page_stats),
        "per_page_stats": page_stats,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"  pages: {len(pages)}")
    print(f"  terms: {len(analysis['terms'])}")
    print(f"  questions: {len(analysis['questions'])}")
    print(f"  topics: {len(analysis['topics'])}")
    print(f"  word range: {analysis['structure']['words']['min']}-{analysis['structure']['words']['max']}")


if __name__ == "__main__":
    main()
