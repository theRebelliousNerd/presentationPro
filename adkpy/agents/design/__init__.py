try:  # pragma: no cover - allows lightweight imports in test environments
    from . import agent  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    agent = None
