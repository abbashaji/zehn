"""Adapter registry: every module in this package that defines Adapter subclasses is auto-discovered."""
from __future__ import annotations

import importlib
import pkgutil
from typing import Dict

from .base import Adapter

REGISTRY: Dict[str, Adapter] = {}


def _discover() -> None:
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
        if info.name == "base":
            continue
        mod = importlib.import_module("%s.%s" % (__name__, info.name))
        for obj in vars(mod).values():
            if isinstance(obj, type) and issubclass(obj, Adapter) and obj is not Adapter and obj.name:
                REGISTRY[obj.name] = obj()


_discover()


def get(name: str) -> Adapter:
    return REGISTRY[name]
