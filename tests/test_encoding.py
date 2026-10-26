from pathlib import Path


def test_polish_sources_are_valid_utf8() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative in ("frontend/index.html", "frontend/views/P4.html", "sprawozdanie_p4/SPRAWOZDANIE-P4.md"):
        content = (root / relative).read_text(encoding="utf-8")
        assert "Projekt" in content
        assert "�" not in content
