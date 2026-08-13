"""Count <img> tags in the main content of each URL.

DataforSEO's content-parsing endpoint returns markdown with image markup stripped,
so we can't get an image count from it. This helper does a direct HTTP fetch + bs4
parse + nav/header/footer stripping, then counts <img> elements in what's left.

The output JSON is keyed by URL: {"https://...": 12, ...}. The analyzer reads this
and merges the counts into per-page stats.

Usage:
    python count_images.py --urls _work/serp.json --out _work/image_counts.json

The --urls input can be either:
  - the SERP response JSON (we walk it for organic URLs that weren't marked "dropped"), OR
  - a plain JSON list of URL strings.

Failures are recorded as None in the output so the analyzer can ignore them.
"""
import argparse
import json
import sys
import time
from pathlib import Path


def extract_urls_from_serp(serp_data):
    """Walk a SERP JSON looking for organic URLs not marked 'dropped'."""
    urls = []

    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "organic" and not obj.get("dropped"):
                u = obj.get("url")
                if u and u.startswith("http"):
                    urls.append(u)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(serp_data)
    return urls


def count_images_for_url(url, timeout=15):
    """Fetch URL and count <img> tags in main content area."""
    import requests
    from bs4 import BeautifulSoup
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code >= 400:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  fetch failed for {url}: {e}", file=sys.stderr)
        return None

    for tag in soup.find_all(["nav", "header", "footer", "aside", "script", "style", "noscript", "form"]):
        tag.decompose()
    main = (soup.find("main") or soup.find("article")
            or soup.find(attrs={"role": "main"}) or soup.find("body") or soup)
    imgs = main.find_all("img")
    # filter out tiny / tracking pixels — anything with width/height <= 2 explicitly set
    real_imgs = []
    for img in imgs:
        try:
            w = int(img.get("width", "0"))
            h = int(img.get("height", "0"))
            if 0 < w <= 2 and 0 < h <= 2:
                continue
        except (TypeError, ValueError):
            pass
        # skip svg pixel-trackers (no src)
        if not img.get("src") and not img.get("data-src"):
            continue
        real_imgs.append(img)
    return len(real_imgs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", required=True, help="Path to SERP JSON or list-of-URLs JSON")
    parser.add_argument("--out", required=True)
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between fetches (s)")
    args = parser.parse_args()

    data = json.loads(Path(args.urls).read_text(encoding="utf-8"))
    if isinstance(data, list):
        urls = [u for u in data if isinstance(u, str) and u.startswith("http")]
    else:
        urls = extract_urls_from_serp(data)

    if not urls:
        print("ERROR: no URLs to fetch.", file=sys.stderr)
        sys.exit(1)

    counts = {}
    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {url[:80]}")
        counts[url] = count_images_for_url(url)
        if args.delay > 0 and i < len(urls):
            time.sleep(args.delay)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(counts, indent=2), encoding="utf-8")
    ok = sum(1 for v in counts.values() if v is not None)
    print(f"\nDone. {ok}/{len(urls)} pages counted.")
    print(f"Output: {args.out}")


if __name__ == "__main__":
    main()
