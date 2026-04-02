import grequests  # noqa: F401  # must import first so gevent patches SSL before asyncio loads it

from app.main import app  # noqa: F401  # re-exported for uvicorn (uvicorn main:app)
