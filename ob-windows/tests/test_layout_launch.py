from __future__ import annotations

from ob_windows.layout import launch


def test_resolve_launch_table_is_case_insensitive():
    assert launch.resolve_launch("Alacritty") == "alacritty"
    assert launch.resolve_launch("THUNAR") == "thunar"
    assert launch.resolve_launch("alacritty_fullscreen") == "ob-furminal"


def test_resolve_launch_unknown_class(monkeypatch):
    monkeypatch.setattr(launch, "_from_desktop", lambda klass, instance: None)
    monkeypatch.setattr(launch.shutil, "which", lambda name: None)
    assert launch.resolve_launch("NoSuchApp") is None
    monkeypatch.setattr(launch.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert launch.resolve_launch("NoSuchApp") == "nosuchapp"


def test_clean_exec_drops_field_codes():
    assert launch._clean_exec("firefox --new-window %u") == "firefox --new-window"
    assert launch._clean_exec("code %F") == "code"


def test_cwd_only_applies_to_terminals(tmp_path):
    cwd = str(tmp_path)
    assert launch.build_launch_cmd("firefox", "firefox", cwd) == "firefox"
    assert launch.build_launch_cmd("kitty", "kitty", None) == "kitty"
    assert launch.build_launch_cmd("kitty", "kitty", "/no/such/dir") == "kitty"


def test_cwd_flag_per_terminal(tmp_path):
    cwd = str(tmp_path)
    assert launch.build_launch_cmd("kitty", "kitty", cwd) == f"kitty --working-directory {cwd}"
    assert (
        launch.build_launch_cmd("alacritty", "Alacritty", cwd)
        == f"alacritty --working-directory {cwd}"
    )
    assert launch.build_launch_cmd("foot", "foot", cwd) == f"foot --working-directory={cwd}"
    assert launch.build_launch_cmd("wezterm", "wezterm", cwd) == f"wezterm start --cwd {cwd}"


def test_cwd_with_spaces_is_quoted(tmp_path):
    d = tmp_path / "my project"
    d.mkdir()
    cmd = launch.build_launch_cmd("kitty", "kitty", str(d))
    assert cmd == f"kitty --working-directory '{d}'"


def test_furminal_is_rebuilt_as_alacritty_with_cwd(tmp_path):
    cmd = launch.build_launch_cmd("ob-furminal", "alacritty_fullscreen", str(tmp_path))
    assert cmd.startswith("alacritty --class 'alacritty_fullscreen,alacritty_fullscreen'")
    assert f"--working-directory {tmp_path}" in cmd
