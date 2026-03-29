from fasthtml.common import *

from app_instance import rt


@rt("/set-theme", methods=["POST"])
def set_theme(req):
    current = req.cookies.get("theme", "light")
    new_theme = "dark" if current == "light" else "light"
    resp = Response(status_code=204)
    resp.set_cookie("theme", new_theme, max_age=60 * 60 * 24 * 365)
    return resp


@rt("/static/{fname:path}")
async def static_files(fname: str):
    return FileResponse(f"static/{fname}")
