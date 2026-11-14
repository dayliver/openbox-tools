from pathlib import Path

from keybinder.models import Category
from keybinder.parse import parse_keyboard_xml, parse_rc
from tests.fixtures.xml_samples import SAMPLE_RC


def test_parse_sample(tmp_path: Path):
    rc = tmp_path / "rc.xml"
    rc.write_text(SAMPLE_RC)
    binds = parse_rc(rc)
    assert len(binds) == 3
    by_key = {b.key: b for b in binds}
    assert by_key["W-Return"].summary() == "alacritty"
    assert by_key["W-Return"].category == Category.APPS
    assert by_key["W-c"].category == Category.WINDOW
    assert by_key["W-space"].category == Category.MENUS


def test_parse_keyboard_fragment():
    from tests.fixtures.xml_samples import STOCK_KEYBOARD

    binds = parse_keyboard_xml(STOCK_KEYBOARD)
    assert len(binds) == 3
