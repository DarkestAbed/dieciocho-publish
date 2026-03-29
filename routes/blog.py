from fasthtml.common import *

from app_instance import rt
from config import SITE_NAME
from domain.posts import ALL_POSTS
from ui.components import page_shell, post_row, not_found_page


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
