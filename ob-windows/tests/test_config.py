from __future__ import annotations

import pytest

from ob_windows.grid.config import DEFAULT_CONFIG, _fractions, load_config


def test_default_config_ships_and_loads():
    assert DEFAULT_CONFIG.is_file()
    cfg = load_config(DEFAULT_CONFIG)
    assert cfg.horizontal[0] == 0.25
    assert cfg.horizontal[-1] == 1.0 and cfg.vertical[-1] == 1.0
    assert cfg.inner_gap == 10
    assert cfg.tolerance_px == 12


def test_fractions_accept_ratio_strings_sort_and_append_full():
    assert _fractions(["1/2", 0.25, "1/2"], axis="horizontal") == (0.25, 0.5, 1.0)


@pytest.mark.parametrize("bad", [0, 1.5, -0.1])
def test_fractions_reject_out_of_range(bad):
    with pytest.raises(ValueError):
        _fractions([bad], axis="vertical")


def test_fractions_reject_empty():
    with pytest.raises(ValueError):
        _fractions([], axis="vertical")


def test_load_config_falls_back_per_key(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[gaps]\ninner = 4\n")
    cfg = load_config(path)
    assert cfg.inner_gap == 4
    assert cfg.horizontal == (0.5, 1.0)
    assert cfg.tolerance_px == 12
