import os
from fasthtml.common import fast_app

DEV = os.environ.get("RAILWAY_ENVIRONMENT") is None
app, rt = fast_app(live=DEV)
