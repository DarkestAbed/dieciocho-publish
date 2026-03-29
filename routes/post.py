from app_instance import rt
from domain.posts import POST_INDEX
from ui.components import page_shell, post_page_content, not_found_page


@rt("/{chapter}/{slug}")
def post_view(chapter: str, slug: str, req):
    post = POST_INDEX.get((chapter, slug))
    if not post:
        return not_found_page(req)
    return page_shell(
        post["title"],
        f"/{chapter}/{slug}",
        post_page_content(post, POST_INDEX),
        req=req,
    )
