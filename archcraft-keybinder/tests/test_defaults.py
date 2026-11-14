from pathlib import Path

from keybinder.defaults import annotate_origins, diff_keybinds, reset_all
from keybinder.models import Origin
from keybinder.parse import parse_keyboard_xml, parse_rc
from keybinder.write import write_rc_with_keyboard
from tests.fixtures.xml_samples import MODIFIED_RC, SAMPLE_RC, STOCK_KEYBOARD


def test_annotate_origins(tmp_path: Path, monkeypatch):
    stock = parse_keyboard_xml(STOCK_KEYBOARD)
    rc = tmp_path / "rc.xml"
    rc.write_text(MODIFIED_RC)
    current = annotate_origins(parse_rc(rc), stock)
    by_key = {b.key: b for b in current}
    assert by_key["W-Return"].origin == Origin.MODIFIED
    assert by_key["W-c"].origin == Origin.STOCK
    assert by_key["W-g"].origin == Origin.CUSTOM


def test_diff(tmp_path: Path):
    stock = parse_keyboard_xml(STOCK_KEYBOARD)
    rc = tmp_path / "rc.xml"
    rc.write_text(MODIFIED_RC)
    result = diff_keybinds(parse_rc(rc), stock)
    assert len(result["modified"]) == 1
    assert result["modified"][0].key == "W-Return"
    assert len(result["custom"]) == 1
    assert result["custom"][0].key == "W-g"
    assert result["missing"] == []


def test_reset_all(tmp_path: Path, monkeypatch):
    rc = tmp_path / "rc.xml"
    rc.write_text(MODIFIED_RC)
    backup_dir = tmp_path / "backups"

    monkeypatch.setattr("keybinder.write.BACKUP_DIR", backup_dir)
    monkeypatch.setattr(
        "keybinder.defaults.stock_keyboard_xml",
        lambda: (STOCK_KEYBOARD, Path("test-stock")),
    )

    info = reset_all(path=rc, dry_run=True)
    assert info["changed"] is True

    info = reset_all(path=rc, dry_run=False, do_backup=True)
    binds = parse_rc(rc)
    assert len(binds) == 3
    assert {b.key for b in binds} == {"W-Return", "W-c", "W-space"}
    assert (backup_dir / info["backup"].split("/")[-1]).exists() or Path(info["backup"]).exists()
    text = rc.read_text()
    assert "<mouse>" in text
    assert "kitty" not in text
    assert "geany" not in text
