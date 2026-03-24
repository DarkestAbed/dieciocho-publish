import os

SITE_NAME = "Dieciocho"
PORT = int(os.environ.get("PORT", 5009))

NAV_LINKS = [
    ("Inicio", "/"),
]

UI_STRINGS = {
    "toggle_theme": "Cambiar tema",
    "read_more": "Leer",
    "back_to_blog": "← Volver",
    "not_found_title": "Página no encontrada",
    "not_found_body": "Este documento no existe.",
    "chapter_label": "Capítulo",
}
