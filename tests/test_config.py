from pathlib import Path

from jobscout.config import AppConfig, load_config


def make_config(**overrides) -> AppConfig:
    defaults = dict(
        roles=["Biochemist", "Lab analyst"],
        include_unspecified=True,
        max_pages_per_query=1,
        request_delay_seconds=0.0,
        sources={
            "profesia": {"keywords": ["Laborant", "Chemik"]},
            "karriere_at": {"keywords": ["Chemiker", "Laborant"]},
            "linkedin": {},
        },
    )
    defaults.update(overrides)
    return AppConfig(**defaults)


def test_queries_for_uses_source_keywords_when_present():
    config = make_config()
    assert config.queries_for("profesia") == ["Laborant", "Chemik"]
    assert config.queries_for("karriere_at") == ["Chemiker", "Laborant"]


def test_queries_for_falls_back_to_global_roles():
    config = make_config()
    assert config.queries_for("linkedin") == ["Biochemist", "Lab analyst"]
    assert config.queries_for("company_pages") == ["Biochemist", "Lab analyst"]


def test_all_keywords_merges_every_language_without_duplicates():
    config = make_config()
    assert config.all_keywords == [
        "Biochemist",
        "Lab analyst",
        "Laborant",
        "Chemik",
        "Chemiker",
    ]


def test_load_config_reads_yaml(tmp_path: Path):
    path = tmp_path / "config.yml"
    path.write_text(
        "roles: [Biochemist]\n"
        "include_unspecified: false\n"
        "sources:\n"
        "  profesia:\n"
        "    region: bratislavsky-kraj\n"
        "    keywords: [Laborant]\n",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.roles == ["Biochemist"]
    assert config.include_unspecified is False
    assert config.queries_for("profesia") == ["Laborant"]
    assert config.sources["profesia"]["region"] == "bratislavsky-kraj"
