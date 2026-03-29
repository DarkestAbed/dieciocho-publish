import re
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

import frontmatter as fm
import mistune

POSTS_DIR = Path("posts")

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

md = mistune.create_markdown(
    plugins=["table", "strikethrough", "task_lists"],
)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def text(self):
        return " ".join(self._parts).split()


def plain_preview(html: str, chars: int = 100) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = " ".join(parser.text())
    return text[:chars] + "…" if len(text) > chars else text


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


def load_posts() -> list[dict]:
    posts = []
    seen_slugs: dict[tuple, str] = {}

    for md_file in POSTS_DIR.glob("*/*.md"):
        chapter = md_file.parent.name
        post = fm.load(str(md_file))

        if not post.get("published", False):
            continue

        title = post.get("title", md_file.stem)
        slug = post.get("slug") or slugify(title)
        key = (chapter, slug)

        if key in seen_slugs:
            raise ValueError(
                f"Slug collision: '{slug}' in chapter '{chapter}' "
                f"({md_file} vs {seen_slugs[key]})"
            )
        seen_slugs[key] = str(md_file)

        date_raw = post.get("date")
        if hasattr(date_raw, "month"):
            date_str = f"{date_raw.day} de {MESES[date_raw.month]} de {date_raw.year}"
        else:
            date_str = str(date_raw)

        posts.append(
            {
                "title": title,
                "slug": slug,
                "chapter": chapter,
                "date": date_raw,
                "date_str": date_str,
                "published": post.get("published", False),
                "content": md(post.content),
                "next_slug": post.get("next"),
                "prev_slug": post.get("prev"),
            }
        )

    posts.sort(key=lambda p: p["date"] or datetime.min, reverse=True)
    return posts


def build_index(posts: list[dict]) -> dict[tuple, dict]:
    return {(p["chapter"], p["slug"]): p for p in posts}


ALL_POSTS = load_posts()
POST_INDEX = build_index(ALL_POSTS)
