from pathlib import Path

import pytest

from keybinder.defaults import (
    DefaultsError,
    annotate_origins,
    diff_keybinds,
    reset_all,
    reset_one,
)
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


def _reset_env(tmp_path: Path, monkeypatch) -> Path:
    rc = tmp_path / "rc.xml"
    rc.write_text(MODIFIED_RC)
    monkeypatch.setattr("keybinder.write.BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(
        "keybinder.defaults.stock_keyboard_xml",
        lambda: (STOCK_KEYBOARD, Path("test-stock")),
    )
    return rc


def test_reset_one_restores_stock(tmp_path: Path, monkeypatch):
    rc = _reset_env(tmp_path, monkeypatch)

    info = reset_one("W-Return", path=rc, dry_run=True)
    assert info == {"dry_run": True, "key": "W-Return", "action": "restore"}
    assert "kitty" in rc.read_text()

    info = reset_one("W-Return", path=rc)
    assert info["action"] == "restore"
    binds = {b.key: b for b in parse_rc(rc)}
    assert binds["W-Return"].summary() == "alacritty"
    # Other keys and other sections are untouched.
    assert binds["W-g"].summary() == "geany"
    assert "<mouse>" in rc.read_text()
    assert "ns0:" not in rc.read_text()


def test_reset_one_custom_needs_flag(tmp_path: Path, monkeypatch):
    rc = _reset_env(tmp_path, monkeypatch)

    with pytest.raises(DefaultsError):
        reset_one("W-g", path=rc)
    assert "geany" in rc.read_text()

    info = reset_one("W-g", path=rc, remove_custom=True)
    assert info["action"] == "remove-custom"
    assert "W-g" not in {b.key for b in parse_rc(rc)}


def test_reset_one_unknown_key(tmp_path: Path, monkeypatch):
    rc = _reset_env(tmp_path, monkeypatch)
    with pytest.raises(KeyError):
        reset_one("W-F12", path=rc)
