from pathlib import Path

from keybinder.mutate import set_execute, update_keybind
from keybinder.parse import parse_rc
from keybinder.write import write_rc_with_keyboard
from tests.fixtures.xml_samples import SAMPLE_RC


def test_update_goto_desktop(tmp_path: Path, monkeypatch):
    rc = tmp_path / "rc.xml"
    rc.write_text(SAMPLE_RC)
    monkeypatch.setattr("keybinder.write.BACKUP_DIR", tmp_path / "backups")

    update_keybind(
        "W-c",
        new_key="W-1",
        action_name="GoToDesktop",
        params={"to": "1"},
        path=rc,
    )
    binds = {b.key: b for b in parse_rc(rc)}
    assert "W-c" not in binds
    assert binds["W-1"].actions[0].name == "GoToDesktop"
    assert binds["W-1"].actions[0].params.get("to") == "1"
    assert "<mouse>" in rc.read_text()


def test_update_execute_command(tmp_path: Path, monkeypatch):
    rc = tmp_path / "rc.xml"
    rc.write_text(SAMPLE_RC)
    monkeypatch.setattr("keybinder.write.BACKUP_DIR", tmp_path / "backups")

    update_keybind(
        "W-Return",
        action_name="Execute",
        params={"command": "kitty"},
        path=rc,
    )
    binds = {b.key: b for b in parse_rc(rc)}
    assert binds["W-Return"].summary() == "kitty"


def test_new_key_has_no_namespace_prefix(tmp_path: Path, monkeypatch):
    """A fresh rc.xml keeps xmlns on <openbox_config> only; new nodes must match."""
    rc = tmp_path / "rc.xml"
    rc.write_text(SAMPLE_RC)
    monkeypatch.setattr("keybinder.write.BACKUP_DIR", tmp_path / "backups")

    set_execute("W-z", "kitty", path=rc)
    update_keybind(
        "W-y",
        action_name="Execute",
        params={"command": "thunar"},
        path=rc,
        create_if_missing=True,
    )
    text = rc.read_text()
    assert "ns0:" not in text
    binds = {b.key: b for b in parse_rc(rc)}
    assert binds["W-z"].summary() == "kitty"
    assert binds["W-y"].summary() == "thunar"
