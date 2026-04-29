#!/usr/bin/env python3
"""Drip-publisher for ListerPros blog drafts.

Reads `_drafts/queue.json`, finds entries whose `publish_date` has arrived,
renders them through `templates/post_template.html`, prepends them to
`posts.json`, regenerates the blog index, and removes them from the queue.

Run daily via GitHub Actions (`.github/workflows/publish-drafts.yml`) or
manually. Idempotent — articles only publish once.

Queue entry schema (in _drafts/queue.json):
  {
    "slug": "drone-photography-tempe",
    "title": "Drone Photography for Tempe Real Estate Listings",
    "meta_description": "...",   # ~150 chars
    "publish_date": "2026-05-02", # ISO date — publishes on/after this date
    "category": "photography_tips",
    "tags": ["..."],
    "featured_image_id": 143,    # references images/blog/ListerPros-{id}.jpg
    "read_time": 7,
    "content_html": "<p>...</p>" # already-rendered article body HTML
  }
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "_drafts" / "queue.json"
TEMPLATES = ROOT / "templates"
POSTS_JSON = ROOT / "posts.json"
INDEX_TEMPLATE = TEMPLATES / "index_template.html"
POST_TEMPLATE = TEMPLATES / "post_template.html"
IMAGE_BASE = "https://cdn.jsdelivr.net/gh/jjnielsen82/listerpros-blog@main/images/blog"


def fill_template(template: str, replacements: dict) -> str:
    out = template
    for k, v in replacements.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def render_related(post: dict, all_posts: list, n: int = 3) -> str:
    """Pick N most-recent same-category posts as 'related'."""
    cat = post.get("category", "")
    siblings = [p for p in all_posts if p.get("category") == cat and p["slug"] != post["slug"]]
    siblings = siblings[:n]
    cards = []
    for s in siblings:
        cards.append(
            f'<a href="/blog/{s["slug"]}" class="block bg-white rounded-2xl p-6 border border-gray-200 hover:border-primary hover:shadow-lg transition">'
            f'<h3 class="font-bold text-lg mb-2">{s["title"]}</h3>'
            f'<p class="text-gray-500 text-sm">Read more &rarr;</p></a>'
        )
    return "\n".join(cards)


def render_post(entry: dict, all_posts: list) -> tuple[str, dict]:
    """Render a queue entry into HTML + posts.json metadata."""
    today = dt.date.today()
    formatted_date = today.strftime("%B %-d, %Y") if sys.platform != "win32" else today.strftime("%B %#d, %Y")

    image_id = entry.get("featured_image_id", 1)
    featured_image = f"{IMAGE_BASE}/ListerPros-{image_id:03d}.jpg"

    template = POST_TEMPLATE.read_text()
    related_html = render_related(entry, all_posts)

    rendered = fill_template(template, {
        "TITLE": entry["title"],
        "META_DESCRIPTION": entry.get("meta_description", entry["title"]),
        "KEYWORDS": ", ".join(entry.get("tags", [])),
        "SLUG": entry["slug"],
        "OG_IMAGE": featured_image,
        "FEATURED_IMAGE": featured_image,
        "PUBLISH_DATE": entry.get("publish_date", today.isoformat()),
        "FORMATTED_DATE": formatted_date,
        "READ_TIME": entry.get("read_time", 6),
        "CATEGORY": entry.get("category", "photography_tips"),
        "TAGS": ", ".join(entry.get("tags", [])),
        "CONTENT": entry["content_html"],
        "RELATED_POSTS": related_html,
    })

    metadata = {
        "slug": entry["slug"],
        "title": entry["title"],
        "excerpt": entry.get("meta_description", entry["title"]),
        "category": entry.get("category", "photography_tips"),
        "date": today.isoformat(),
        "formatted_date": formatted_date,
        "read_time": entry.get("read_time", 6),
        "featured_image": featured_image,
        "tags": entry.get("tags", []),
        "filename": entry["slug"] + ".html",
    }
    return rendered, metadata


def regenerate_index(posts: list):
    template = INDEX_TEMPLATE.read_text()
    # Featured = most recent post
    if not posts:
        return
    featured = posts[0]

    # Latest articles list (next ~12)
    article_cards = []
    for p in posts[1:13]:
        article_cards.append(
            f'<a href="/blog/{p["slug"]}" class="group block bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition card-lift">'
            f'<div class="aspect-[16/9] overflow-hidden"><img src="{p["featured_image"]}" alt="{p["title"]}" class="w-full h-full object-cover group-hover:scale-105 transition" loading="lazy"></div>'
            f'<div class="p-6">'
            f'<div class="text-xs text-primary font-semibold mb-2 uppercase tracking-wider">{p["category"].replace("_"," ")}</div>'
            f'<h3 class="font-bold text-lg mb-2 group-hover:text-primary transition">{p["title"]}</h3>'
            f'<p class="text-gray-500 text-sm mb-3">{p["excerpt"][:140]}...</p>'
            f'<div class="text-xs text-gray-400">{p["formatted_date"]} &middot; {p["read_time"]} min read</div>'
            f'</div></a>'
        )

    rendered = fill_template(template, {
        "FEATURED_TITLE": featured["title"],
        "FEATURED_EXCERPT": featured["excerpt"],
        "FEATURED_IMAGE": featured["featured_image"],
        "FEATURED_SLUG": featured["slug"],
        "FEATURED_DATE": featured["formatted_date"],
        "FEATURED_READ_TIME": featured["read_time"],
        "FEATURED_CATEGORY": featured["category"].replace("_", " "),
        "ARTICLE_CARDS": "\n".join(article_cards),
        "TOTAL_POSTS": len(posts),
    })
    (ROOT / "index.html").write_text(rendered)


def main():
    if not QUEUE.exists():
        print(f"no queue at {QUEUE}, nothing to publish")
        return

    queue = json.loads(QUEUE.read_text())
    today = dt.date.today()
    posts = json.loads(POSTS_JSON.read_text())

    to_publish = []
    remaining = []
    for entry in queue:
        try:
            pdate = dt.date.fromisoformat(entry["publish_date"])
        except Exception:
            print(f"warn: bad publish_date in {entry.get('slug', '<unknown>')}, skipping")
            remaining.append(entry)
            continue
        if pdate <= today:
            to_publish.append(entry)
        else:
            remaining.append(entry)

    if not to_publish:
        print(f"nothing due today ({today}). {len(remaining)} entries still queued.")
        return

    print(f"publishing {len(to_publish)} draft(s) due as of {today}")
    for entry in to_publish:
        slug = entry["slug"]
        # Skip if already published (idempotent guard)
        if any(p["slug"] == slug for p in posts):
            print(f"  skip {slug} — already in posts.json")
            continue
        html, meta = render_post(entry, posts)
        out_path = ROOT / f"{slug}.html"
        out_path.write_text(html)
        # Prepend to posts.json so it shows newest-first
        posts.insert(0, meta)
        print(f"  published {slug}")

    POSTS_JSON.write_text(json.dumps(posts, indent=2, ensure_ascii=False))
    QUEUE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))
    regenerate_index(posts)
    print(f"\ndone. {len(posts)} total posts, {len(remaining)} still queued.")


if __name__ == "__main__":
    main()
