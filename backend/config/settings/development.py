from .base import *
import sys

DEBUG = True

INSTALLED_APPS += [
    # Development tools can be added here
]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Database - PostgreSQL for all environments
# Override with SQLite for tests if needed
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://postgres:1234@localhost:5432/ea_fc_platform"),
}

if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }
