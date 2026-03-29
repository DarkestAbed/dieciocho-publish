import os
import re
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

import frontmatter as fm
import mistune
from fasthtml.common import *

from config import SITE_NAME, PORT, NAV_LINKS, UI_STRINGS

# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

md = mistune.create_markdown(
    plugins=["table", "strikethrough", "task_lists"],
)

# ---------------------------------------------------------------------------
# Post loading
# ---------------------------------------------------------------------------

POSTS_DIR = Path("posts")

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


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


def build_index() -> dict[tuple, dict]:
    return {(p["chapter"], p["slug"]): p for p in load_posts()}


ALL_POSTS = load_posts()
POST_INDEX = build_index()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

DEV = os.environ.get("RAILWAY_ENVIRONMENT") is None
app, rt = fast_app(live=DEV)

COMMON_HDRS = (
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css"),
    Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap"),
    Link(rel="stylesheet", href="/static/custom.css"),
    Script("""
        (function() {
            var t = document.cookie.match(/theme=([^;]+)/);
            if (t) document.documentElement.setAttribute('data-theme', t[1]);
        })();

        function toggleTheme() {
            var current = document.documentElement.getAttribute('data-theme') || 'light';
            var next = current === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', next);
        }
    """),
)

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def get_chapters() -> list[str]:
    """Chapters sorted by the date of their earliest post."""
    earliest: dict[str, object] = {}
    for p in ALL_POSTS:
        ch = p["chapter"]
        if ch not in earliest or p["date"] < earliest[ch]:
            earliest[ch] = p["date"]
    return sorted(earliest, key=lambda ch: earliest[ch])


def chapter_sidebar(current_path: str = "/"):
    chapters = get_chapters()
    items = []
    for ch in chapters:
        href = f"/{ch}/"
        active = current_path == href or current_path.startswith(f"/{ch}/")
        items.append(
            Li(A(ch, href=href, cls=f"sidebar-link{'  sidebar-link--active' if active else ''}"))
        )
    return Aside(
        Nav(
            Ul(*items, cls="sidebar-list"),
        ),
        cls="chapter-sidebar",
    )


def nav_bar(current_path: str = "/"):
    links = [A(label, href=href, cls="nav-link") for label, href in NAV_LINKS]
    theme_btn = Button(
        UI_STRINGS["toggle_theme"],
        hx_post="/set-theme",
        hx_swap="none",
        cls="theme-toggle",
        onclick="toggleTheme(this)",
    )
    return Nav(
        Div(A(SITE_NAME, href="/", cls="site-title"), cls="nav-brand"),
        Div(*links, theme_btn, cls="nav-links"),
        cls="site-nav",
    )


def post_row(post: dict):
    url = f"/{post['chapter']}/{post['slug']}"
    preview = plain_preview(post["content"])
    return Article(
        Div(
            Span(post["date_str"], cls="post-date"),
            cls="post-meta",
        ),
        A(f"{post['chapter']} / {post['slug']}", href=url, cls="chapter-label post-pill-link"),
        P(preview, cls="post-preview") if preview else None,
        cls="post-row",
    )


def post_page_content(post: dict, post_index: dict):
    chapter = post["chapter"]
    prev_post = post_index.get((chapter, post["prev_slug"])) if post.get("prev_slug") else None
    next_post = post_index.get((chapter, post["next_slug"])) if post.get("next_slug") else None

    nav_items = []
    if prev_post:
        nav_items.append(
            A(f"← {prev_post['title']}", href=f"/{chapter}/{prev_post['slug']}", cls="post-nav-prev")
        )
    if next_post:
        nav_items.append(
            A(f"{next_post['title']} →", href=f"/{chapter}/{next_post['slug']}", cls="post-nav-next")
        )

    return Main(
        Article(
            Header(
                Div(
                    Span(chapter, cls="chapter-label"),
                    Span(post["date_str"], cls="post-date"),
                    cls="post-meta",
                ),
                H1(post["title"]),
                cls="post-header",
            ),
            Div(NotStr(post["content"]), cls="post-body"),
            Footer(
                Div(*nav_items, cls="post-nav") if nav_items else None,
                A(UI_STRINGS["back_to_blog"], href="/", cls="back-link"),
                cls="post-footer",
            ),
        ),
        cls="post-page",
    )


def page_shell(title: str, current_path: str, *content, req=None):
    theme = req.cookies.get("theme", "light") if req else "light"
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title(f"{title} — {SITE_NAME}"),
            *COMMON_HDRS,
        ),
        Body(
            nav_bar(current_path),
            Div(
                chapter_sidebar(current_path),
                Div(*content, cls="main-content"),
                cls="layout",
            ),
            Footer(
                P(f"© {SITE_NAME}", cls="footer-copy"),
                cls="site-footer",
            ),
        ),
        data_theme=theme,
    )


def not_found_page(req=None):
    return page_shell(
        UI_STRINGS["not_found_title"],
        "/",
        Main(
            H2(UI_STRINGS["not_found_title"]),
            P(UI_STRINGS["not_found_body"]),
            A(UI_STRINGS["back_to_blog"], href="/"),
            cls="not-found",
        ),
        req=req,
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@rt("/")
def index(req):
    sorted_posts = sorted(ALL_POSTS, key=lambda p: (p["chapter"], p["date"]))
    rows = [post_row(p) for p in sorted_posts]
    return page_shell(
        SITE_NAME,
        "/",
        Main(
            Div(*rows, cls="post-list") if rows else P("Próximamente."),
            cls="blog-index",
        ),
        req=req,
    )


@rt("/{chapter}/")
def chapter_index(chapter: str, req):
    posts = sorted(
        [p for p in ALL_POSTS if p["chapter"] == chapter],
        key=lambda p: p["date"],
    )
    if not posts:
        return not_found_page(req)
    rows = [post_row(p) for p in posts]
    return page_shell(
        chapter,
        f"/{chapter}/",
        Main(
            H2(chapter, cls="chapter-heading"),
            Div(*rows, cls="post-list"),
            cls="blog-index",
        ),
        req=req,
    )


@rt("/{chapter}/{slug}")
def post_view(chapter: str, slug: str, req):
    post = POST_INDEX.get((chapter, slug))
    if not post:
        return not_found_page(req)
    return page_shell(post["title"], f"/{chapter}/{slug}", post_page_content(post, POST_INDEX), req=req)


@rt("/static/{fname:path}")
async def static_files(fname: str):
    return FileResponse(f"static/{fname}")


@rt("/set-theme", methods=["POST"])
def set_theme(req):
    current = req.cookies.get("theme", "light")
    new_theme = "dark" if current == "light" else "light"
    resp = Response(status_code=204)
    resp.set_cookie("theme", new_theme, max_age=60 * 60 * 24 * 365)
    return resp


if __name__ == "__main__":
    serve(port=PORT)
