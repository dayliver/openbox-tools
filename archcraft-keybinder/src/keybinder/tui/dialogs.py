"""Modal dialogs for the keybinder TUI."""

from __future__ import annotations

from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from keybinder.models import Action, Keybind

# Common Openbox actions for the Select; custom names can still be typed in params flow.
COMMON_ACTIONS: list[tuple[str, str]] = [
    ("Execute", "Execute"),
    ("ShowMenu", "ShowMenu"),
    ("GoToDesktop", "GoToDesktop"),
    ("SendToDesktop", "SendToDesktop"),
    ("NextWindow", "NextWindow"),
    ("PreviousWindow", "PreviousWindow"),
    ("Close", "Close"),
    ("Iconify", "Iconify"),
    ("ToggleMaximize", "ToggleMaximize"),
    ("ToggleFullscreen", "ToggleFullscreen"),
    ("ToggleShowDesktop", "ToggleShowDesktop"),
    ("MaximizeFull", "MaximizeFull"),
    ("UnmaximizeFull", "UnmaximizeFull"),
    ("MoveRelative", "MoveRelative"),
    ("ResizeRelative", "ResizeRelative"),
    ("MoveResizeTo", "MoveResizeTo"),
    ("AddDesktop", "AddDesktop"),
    ("RemoveDesktop", "RemoveDesktop"),
    ("Reconfigure", "Reconfigure"),
    ("Restart", "Restart"),
    ("Exit", "Exit"),
]

# Suggested param fields per action (always merged with existing params).
SUGGESTED_PARAMS: dict[str, list[str]] = {
    "Execute": ["command"],
    "ShowMenu": ["menu"],
    "GoToDesktop": ["to", "wrap"],
    "SendToDesktop": ["to", "wrap"],
    "AddDesktop": ["where"],
    "RemoveDesktop": ["where"],
    "MoveRelative": ["x", "y"],
    "ResizeRelative": ["left", "right", "top", "bottom"],
    "MoveResizeTo": ["x", "y", "width", "height"],
    "NextWindow": ["dialog", "allDesktops", "interactive"],
    "PreviousWindow": ["dialog", "allDesktops", "interactive"],
    "Exit": ["prompt"],
}


@dataclass
class KeybindEditResult:
    old_key: str
    new_key: str
    action_name: str
    params: dict[str, str] = field(default_factory=dict)


class ConfirmModal(ModalScreen[bool]):
    """Yes/No confirmation. Dismisses with True/False."""

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }
    ConfirmModal > Vertical {
        width: 64;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    ConfirmModal .question {
        margin-bottom: 1;
    }
    ConfirmModal #actions {
        height: 3;
        width: 100%;
        align: center middle;
    }
    ConfirmModal #actions Button {
        margin: 0 1;
        min-width: 14;
        height: 3;
    }
    """

    def __init__(self, message: str, *, confirm_label: str = "Confirm") -> None:
        super().__init__()
        self.message = message
        self.confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.message, classes="question")
            with Horizontal(id="actions"):
                yield Button(self.confirm_label, variant="error", id="yes")
                yield Button("Cancel", variant="primary", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss(False)


class EditKeybindModal(ModalScreen[KeybindEditResult | None]):
    """Edit key chord, primary action, and its parameters."""

    BINDINGS = [
        Binding("enter", "save", "Save", show=False, priority=True),
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    EditKeybindModal {
        align: center middle;
    }
    EditKeybindModal > Vertical {
        width: 78;
        height: auto;
        max-height: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    EditKeybindModal Label {
        margin-top: 1;
    }
    EditKeybindModal Input, EditKeybindModal Select {
        margin-bottom: 0;
    }
    EditKeybindModal #param-box {
        height: auto;
        max-height: 14;
        margin-top: 1;
    }
    EditKeybindModal .hint {
        color: $text-muted;
        margin-top: 1;
    }
    EditKeybindModal #actions {
        height: 3;
        width: 100%;
        align: center middle;
        margin-top: 1;
    }
    EditKeybindModal #actions Button {
        margin: 0 1;
        min-width: 14;
        height: 3;
    }
    """

    def __init__(self, bind: Keybind) -> None:
        super().__init__()
        self.bind = bind
        primary = bind.actions[0] if bind.actions else Action(name="Execute")
        self._primary = primary
        self._current_action = primary.name
        self._param_names = self._param_names_for(primary.name, primary.params)
        self._select_ready = False

    @staticmethod
    def _param_names_for(action_name: str, existing: dict[str, str]) -> list[str]:
        suggested = SUGGESTED_PARAMS.get(action_name, [])
        names: list[str] = []
        for name in list(suggested) + sorted(existing):
            if name not in names:
                names.append(name)
        if not names:
            names = ["value"]
        return names

    def compose(self) -> ComposeResult:
        extras = len(self.bind.actions) - 1
        with Vertical():
            yield Label(f"Edit keybind  [b]{self.bind.key}[/b]")
            yield Label("Key")
            yield Input(value=self.bind.key, id="key", placeholder="e.g. W-1  C-A-Right  A-F4")
            yield Label("Primary action")
            options = list(COMMON_ACTIONS)
            if self._primary.name and self._primary.name not in {a[1] for a in COMMON_ACTIONS}:
                options.insert(0, (self._primary.name, self._primary.name))
            yield Select(
                options,
                value=self._primary.name if self._primary.name else Select.BLANK,
                id="action",
                allow_blank=False,
            )
            yield Label("Parameters")
            with VerticalScroll(id="param-box"):
                for name in self._param_names:
                    yield Label(name)
                    yield Input(
                        value=self._primary.params.get(name, ""),
                        id=f"param-{name}",
                        placeholder=name,
                    )
            if extras > 0:
                other = ", ".join(a.name for a in self.bind.actions[1:])
                yield Static(
                    f"Also keeps {extras} sibling action(s): {other}",
                    classes="hint",
                )
            yield Static(
                "Tip: Enter save · Esc cancel · GoToDesktop to=1..N or next/previous",
                classes="hint",
            )
            with Horizontal(id="actions"):
                yield Button("Save", variant="success", id="save", flat=False)
                yield Button("Cancel", variant="default", id="cancel", flat=False)

    def on_mount(self) -> None:
        self._select_ready = True
        self.query_one("#key", Input).focus()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "action" or not self._select_ready:
            return
        action_name = str(event.value)
        if action_name == self._current_action:
            return
        self._current_action = action_name
        current_vals = self._collect_params()
        self._param_names = self._param_names_for(action_name, current_vals)
        box = self.query_one("#param-box", VerticalScroll)
        await box.remove_children()
        mounts = []
        for name in self._param_names:
            mounts.append(Label(name))
            mounts.append(
                Input(
                    value=current_vals.get(name, "")
                    or self._primary.params.get(name, ""),
                    id=f"param-{name}",
                    placeholder=name,
                )
            )
        await box.mount(*mounts)

    def _collect_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for name in self._param_names:
            widget_id = f"#param-{name}"
            try:
                params[name] = self.query_one(widget_id, Input).value.strip()
            except Exception:
                continue
        return params

    def _result(self) -> KeybindEditResult | None:
        new_key = self.query_one("#key", Input).value.strip()
        action_widget = self.query_one("#action", Select)
        action_name = str(action_widget.value) if action_widget.value is not Select.BLANK else ""
        if not new_key or not action_name:
            return None
        return KeybindEditResult(
            old_key=self.bind.key,
            new_key=new_key,
            action_name=action_name,
            params=self._collect_params(),
        )

    def action_save(self) -> None:
        result = self._result()
        if result is None:
            self.notify("Key and action are required", severity="warning")
            return
        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()


class MessageModal(ModalScreen[None]):
    """Simple notice."""

    DEFAULT_CSS = """
    MessageModal {
        align: center middle;
    }
    MessageModal > Vertical {
        width: 60;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    MessageModal Button {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.message)
            yield Button("OK", variant="primary", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key in {"escape", "enter"}:
            self.dismiss(None)
