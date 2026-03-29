from app_instance import app  # noqa: F401 — `app` must be in this module's namespace for serve()
from config import PORT
from fasthtml.common import serve

import routes.blog   # noqa: F401 — registers @rt decorators
import routes.post   # noqa: F401
import routes.theme  # noqa: F401

if __name__ == "__main__":
    serve(port=PORT)
