from __future__ import annotations

import pytest

from ob_windows.layout import store


@pytest.fixture(autouse=True)
def preset_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "PRESET_DIR", tmp_path / "presets")
    return tmp_path / "presets"


def test_save_load_list_delete(preset_dir):
    assert store.list_presets() == []
    path = store.save_preset("coding", {"desktop": 1, "windows": [{"class": "kitty"}]})
    assert path == preset_dir / "coding.json"

    data = store.load_preset("coding")
    assert data["name"] == "coding"
    assert data["version"] == 1
    assert data["desktop"] == 1
    assert data["windows"] == [{"class": "kitty"}]
    assert "saved_at" in data

    store.save_preset("한글 이름", {"desktop": 0, "windows": []})
    assert store.list_presets() == ["coding", "한글 이름"]

    store.delete_preset("coding")
    assert store.list_presets() == ["한글 이름"]


@pytest.mark.parametrize("bad", ["", "   ", "../escape", "a/b", "x" * 65, "semi;colon"])
def test_unsafe_names_are_rejected(bad):
    with pytest.raises(ValueError):
        store.save_preset(bad, {"windows": []})


def test_missing_preset_errors():
    with pytest.raises(FileNotFoundError):
        store.load_preset("nope")
    with pytest.raises(FileNotFoundError):
        store.delete_preset("nope")
