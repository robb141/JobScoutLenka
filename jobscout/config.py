from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    roles: list[str]
    include_unspecified: bool
    max_pages_per_query: int
    request_delay_seconds: float
    sources: dict[str, dict[str, Any]]

    def queries_for(self, source_key: str) -> list[str]:
        """Search terms to send to one source.

        Each board speaks a different language, so a source may override the
        global ``roles`` with its own ``keywords`` list (Slovak for Profesia,
        German for karriere.at). Falls back to ``roles`` when it does not.
        """
        keywords = self.sources.get(source_key, {}).get("keywords")
        cleaned = [str(term).strip() for term in keywords or [] if str(term).strip()]
        return cleaned or self.roles

    @property
    def all_keywords(self) -> list[str]:
        """Every role term in any language - the global list plus every
        per-source ``keywords`` override. Used for matching (not searching),
        so a German title still resolves against a German keyword."""
        terms = list(self.roles)
        for settings in self.sources.values():
            for term in settings.get("keywords") or []:
                text = str(term).strip()
                if text and text not in terms:
                    terms.append(text)
        return terms


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    return AppConfig(
        roles=[str(role).strip() for role in data.get("roles", []) if str(role).strip()],
        include_unspecified=bool(data.get("include_unspecified", True)),
        max_pages_per_query=int(data.get("max_pages_per_query", 3)),
        request_delay_seconds=float(data.get("request_delay_seconds", 1.0)),
        sources=data.get("sources", {}),
    )
