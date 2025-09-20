try:  # pragma: no cover - allow lightweight imports during local testing
    from . import agent  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    agent = None
