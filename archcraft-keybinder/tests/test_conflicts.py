from keybinder.conflicts import find_conflicts
from keybinder.models import Action, Keybind


def test_conflicts():
    binds = [
        Keybind(key="W-a", actions=[Action("Close")]),
        Keybind(key="W-a", actions=[Action("Execute", {"command": "x"})]),
        Keybind(key="W-b", actions=[Action("Close")]),
    ]
    conflicts = find_conflicts(binds)
    assert list(conflicts.keys()) == ["W-a"]
    assert len(conflicts["W-a"]) == 2
    assert find_conflicts(binds, "W-b") == {}
