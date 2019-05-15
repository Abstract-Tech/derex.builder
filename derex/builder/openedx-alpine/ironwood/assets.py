"""
Bare minimum settings for collecting production assets.
"""
# type: ignore
from ..common import *
from openedx.core.lib.derived import derive_settings


COMPREHENSIVE_THEME_DIRS.append("/openedx/themes")
STATIC_ROOT_BASE = "/openedx/staticfiles"
STATIC_ROOT = {"lms": path(STATIC_ROOT_BASE), "cms": path(STATIC_ROOT_BASE) / "studio"}[
    SERVICE_VARIANT
]
WEBPACK_LOADER["DEFAULT"]["STATS_FILE"] = STATIC_ROOT / "webpack-stats.json"

SECRET_KEY = "secret"
XQUEUE_INTERFACE = {"django_auth": None, "url": None}
DATABASES = {"default": {}}
derive_settings(__name__)
