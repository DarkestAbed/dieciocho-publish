from fasthtml.common import *

from config import SITE_NAME, NAV_LINKS, UI_STRINGS
from domain.posts import ALL_POSTS, plain_preview

COMMON_HDRS = (
    Script(src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/dist/htmx.js"),
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


def get_chapters() -> list[str]:
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
