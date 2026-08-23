import textwrap
from pathlib import Path

from src.ast_parser import analyze_file


def test_detects_percent_string_formatting(tmp_path: Path) -> None:
    source = "msg = 'hello %s' % name\n"
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    findings = analyze_file(file_path)

    assert any(f.pattern == "percent-string-formatting" for f in findings)


def test_detects_bare_except(tmp_path: Path) -> None:
    source = textwrap.dedent(
        """
        try:
            risky()
        except:
            pass
        """
    )
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    findings = analyze_file(file_path)

    assert any(f.pattern == "bare-except" for f in findings)


def test_detects_mutable_default_argument(tmp_path: Path) -> None:
    source = "def add_item(item, items=[]):\n    items.append(item)\n"
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    findings = analyze_file(file_path)

    assert any(f.pattern == "mutable-default-argument" for f in findings)


def test_clean_file_has_no_findings(tmp_path: Path) -> None:
    source = "def add(a: int, b: int) -> int:\n    return a + b\n"
    file_path = tmp_path / "sample.py"
    file_path.write_text(source)

    findings = analyze_file(file_path)

    assert findings == []
