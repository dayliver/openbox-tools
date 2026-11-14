"""Textual TUI for Archcraft keybinder."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Static,
    Tab,
    TabbedContent,
    TabPane,
    Tabs,
)

from keybinder.apply import apply_changes
from keybinder.defaults import DefaultsError, load_current, reset_all, reset_one
from keybinder.models import Category, Keybind, Origin
from keybinder.mutate import MutateError, remove_key, update_keybind
from keybinder.paths import RC_XML
from keybinder.tui.dialogs import ConfirmModal, EditKeybindModal, KeybindEditResult

TAB_ORDER: list[tuple[str, str | None]] = [
    ("all", None),
    ("apps", Category.APPS.value),
    ("window", Category.WINDOW.value),
    ("menus", Category.MENUS.value),
    ("hardware", Category.HARDWARE.value),
    ("session", Category.SESSION.value),
    ("other", Category.OTHER.value),
    ("changed", "__changed__"),
]


class KeybinderApp(App[None]):
    """Browse and edit Openbox keybinds."""

    TITLE = "Archcraft Keybinder"
    CSS = """
    Screen {
        layout: vertical;
    }
    #toolbar {
        height: auto;
        padding: 0 1;
        background: $boost;
    }
    #search {
        width: 1fr;
    }
    #status {
        height: auto;
        padding: 0 1;
        color: $text-muted;
    }
    #tabs {
        height: 1fr;
    }
    TabPane {
        padding: 0;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search", key_display="/"),
        Binding("tab", "cycle_focus", show=False, priority=True),
        Binding("shift+tab", "cycle_focus", show=False, priority=True),
        Binding("escape", "focus_table", "Table", show=False),
        Binding("down", "focus_table_from_chrome", "Table", show=False),
        Binding("left", "nav_left", show=False, priority=True),
        Binding("right", "nav_right", show=False, priority=True),
        Binding("enter", "edit", "Edit", priority=True),
        Binding("e", "edit", show=False),  # alias
        Binding("r", "reset_one", "Reset key"),
        Binding("R", "reset_all", "Reset all"),
        Binding("d", "delete", "Delete"),
        Binding("a", "apply", "Apply"),
        Binding("f5", "reload", "Reload"),
    ]

    def __init__(self, rc_path: Path | None = None) -> None:
        super().__init__()
        self.rc_path = rc_path or RC_XML
        self.keybinds: list[Keybind] = []
        self._columns_ready: set[str] = set()
        self._keep_search_focus = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="toolbar"):
            yield Input(placeholder="Filter keys / commands…", id="search")
        with TabbedContent(id="tabs"):
            for tab_id, _ in TAB_ORDER:
                label = tab_id if tab_id != "changed" else "modified"
                with TabPane(label, id=f"tab-{tab_id}"):
                    yield DataTable(
                        id=f"table-{tab_id}",
                        cursor_type="row",
                        zebra_stripes=True,
                    )
        yield Static("", id="status")
        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # Let modal screens own Enter/Esc/←→/Tab (app priority bindings otherwise steal them).
        if isinstance(self.screen, ModalScreen):
            if action in {
                "edit",
                "nav_left",
                "nav_right",
                "cycle_focus",
                "focus_table",
                "focus_table_from_chrome",
                "focus_search",
                "reset_one",
                "reset_all",
                "delete",
                "apply",
                "reload",
            }:
                return False
        return True

    def on_mount(self) -> None:
        # Category tabs: mouse + ←→ only — never in Tab-key focus order.
        self.query_one(Tabs).can_focus = False
        for tab in self.query(Tab):
            tab.can_focus = False
        self.reload_data()
        self.call_after_refresh(self._focus_active_table)

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_focus_table(self) -> None:
        self._focus_active_table()

    def action_cycle_focus(self) -> None:
        """Tab toggles search ↔ table only (skips category tab bar)."""
        focused = self.focused
        if isinstance(focused, Input) and focused.id == "search":
            self._focus_active_table()
        else:
            self.action_focus_search()

    def action_focus_table_from_chrome(self) -> None:
        """↓ from search moves into the keybind table."""
        focused = self.focused
        if isinstance(focused, DataTable):
            return
        self._focus_active_table()

    def action_nav_left(self) -> None:
        if self._nav_search_caret(-1):
            return
        keep = isinstance(self.focused, Input) and self.focused.id == "search"
        self._switch_tab(-1, keep_search_focus=keep)

    def action_nav_right(self) -> None:
        if self._nav_search_caret(1):
            return
        keep = isinstance(self.focused, Input) and self.focused.id == "search"
        self._switch_tab(1, keep_search_focus=keep)

    def _nav_search_caret(self, delta: int) -> bool:
        """Move caret inside search; return True if the key was consumed for typing."""
        focused = self.focused
        if not isinstance(focused, Input) or focused.id != "search":
            return False
        pos = focused.cursor_position
        if delta < 0:
            if pos > 0:
                focused.cursor_position = pos - 1
                return True
            return False  # at start → tab switch
        if pos < len(focused.value):
            focused.cursor_position = pos + 1
            return True
        return False  # at end → tab switch

    def _switch_tab(self, delta: int, *, keep_search_focus: bool = False) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        ids = [f"tab-{tid}" for tid, _ in TAB_ORDER]
        current = tabs.active or ids[0]
        try:
            idx = ids.index(current)
        except ValueError:
            idx = 0
        self._keep_search_focus = keep_search_focus
        tabs.active = ids[(idx + delta) % len(ids)]

    def action_reload(self) -> None:
        self.reload_data()
        self.notify("Reloaded", severity="information")

    def reload_data(
        self,
        *,
        select_key: str | None = None,
        select_row: int | None = None,
    ) -> None:
        self.keybinds = load_current(self.rc_path)
        self.refresh_all_tables()
        self._update_status()

        def after() -> None:
            self._focus_active_table()
            if select_key:
                self._select_key(select_key)
            elif select_row is not None:
                table = self._active_table()
                if table.row_count > 0:
                    table.move_cursor(
                        row=min(max(select_row, 0), table.row_count - 1),
                        scroll=True,
                    )

        self.call_after_refresh(after)

    def _select_key(self, key: str) -> None:
        """Move cursor to the row for ``key`` in every table that contains it."""
        for tab_id, _ in TAB_ORDER:
            table = self.query_one(f"#table-{tab_id}", DataTable)
            try:
                row = table.get_row_index(key)
            except Exception:
                continue
            table.move_cursor(row=row, scroll=True)
        # Ensure active table keeps focus after cursor moves
        self._active_table().focus()

    def _focus_active_table(self) -> None:
        table = self._active_table()
        table.focus()
        if table.row_count > 0 and table.cursor_row < 0:
            table.move_cursor(row=0)

    def _filter_query(self) -> str:
        return self.query_one("#search", Input).value.strip().lower()

    def _filtered(self, category: str | None) -> list[Keybind]:
        q = self._filter_query()
        rows = self.keybinds
        if category == "__changed__":
            rows = [b for b in rows if b.origin != Origin.STOCK]
        elif category is not None:
            rows = [b for b in rows if b.category.value == category]
        if q:
            rows = [
                b
                for b in rows
                if q in b.key.lower()
                or q in b.summary().lower()
                or q in b.category.value
                or q in b.origin.value
            ]
        return rows

    def refresh_all_tables(self) -> None:
        for tab_id, category in TAB_ORDER:
            table = self.query_one(f"#table-{tab_id}", DataTable)
            self._fill_table(table, tab_id, self._filtered(category))

    def _fill_table(self, table: DataTable, tab_id: str, binds: list[Keybind]) -> None:
        if tab_id not in self._columns_ready:
            table.add_columns("Key", "Category", "Status", "Action")
            self._columns_ready.add(tab_id)
        table.clear()
        for bind in binds:
            table.add_row(
                bind.key,
                bind.category.value,
                bind.origin.value,
                bind.summary(),
                key=bind.key,
            )

    def _update_status(self) -> None:
        total = len(self.keybinds)
        modified = sum(1 for b in self.keybinds if b.origin == Origin.MODIFIED)
        custom = sum(1 for b in self.keybinds if b.origin == Origin.CUSTOM)
        self.query_one("#status", Static).update(
            f"{self.rc_path}  ·  {total} keys  ·  "
            f"{modified} modified  ·  {custom} custom  ·  "
            f"[enter] edit  [←→] tabs  [r]eset  [d]elete  [a]pply  [/] search"
        )

    @on(Input.Changed, "#search")
    def on_search_changed(self, _event: Input.Changed) -> None:
        self.refresh_all_tables()

    @on(TabbedContent.TabActivated, "#tabs")
    def on_tab_activated(self, _event: TabbedContent.TabActivated) -> None:
        if self._keep_search_focus:
            self._keep_search_focus = False
            self.call_after_refresh(lambda: self.query_one("#search", Input).focus())
            return
        # Tab bar keeps focus after mouse/shortcut tab changes; hand it to the pane table.
        self.call_after_refresh(self._focus_active_table)

    def _active_table(self) -> DataTable:
        tabs = self.query_one("#tabs", TabbedContent)
        pane_id = tabs.active
        # active is like "tab-apps"
        tab_key = pane_id.removeprefix("tab-") if pane_id else "all"
        return self.query_one(f"#table-{tab_key}", DataTable)

    def _selected_key(self) -> str | None:
        table = self._active_table()
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        if row_key is None or row_key.value is None:
            return None
        return str(row_key.value)

    def _bind_for(self, key: str) -> Keybind | None:
        for bind in self.keybinds:
            if bind.key == key:
                return bind
        return None

    def _apply_live(self) -> None:
        """Reload Openbox so rc.xml edits take effect immediately."""
        try:
            info = apply_changes()
        except FileNotFoundError as exc:
            self.notify(str(exc), severity="error")
            return
        if info["reconfigure_returncode"] != 0:
            err = info.get("reconfigure_stderr") or f"exit {info['reconfigure_returncode']}"
            self.notify(f"Saved file, but reconfigure failed: {err}", severity="error")

    def action_edit(self) -> None:
        if not isinstance(self.focused, DataTable):
            return
        key = self._selected_key()
        if not key:
            self.notify("No row selected", severity="warning")
            return
        bind = self._bind_for(key)
        if not bind:
            return

        def on_result(result: KeybindEditResult | None) -> None:
            if result is None:
                return
            try:
                update_keybind(
                    result.old_key,
                    new_key=result.new_key,
                    action_name=result.action_name,
                    params=result.params,
                    path=self.rc_path,
                )
            except (MutateError, KeyError) as exc:
                self.notify(str(exc), severity="error")
                return
            self.reload_data(select_key=result.new_key)
            self._apply_live()
            self.notify(
                f"Applied {result.old_key}"
                + (f" → {result.new_key}" if result.new_key != result.old_key else ""),
                severity="information",
            )

        self.push_screen(EditKeybindModal(bind), on_result)

    def action_delete(self) -> None:
        key = self._selected_key()
        if not key:
            self.notify("No row selected", severity="warning")
            return

        def on_confirm(ok: bool | None) -> None:
            if not ok:
                return
            row = self._active_table().cursor_row
            try:
                remove_key(key, path=self.rc_path)
            except KeyError as exc:
                self.notify(str(exc), severity="error")
                return
            self.reload_data(select_row=row)
            self._apply_live()
            self.notify(f"Removed {key}", severity="warning")

        self.push_screen(
            ConfirmModal(f"Delete keybind [b]{key}[/b]?", confirm_label="Delete"),
            on_confirm,
        )

    def action_reset_one(self) -> None:
        key = self._selected_key()
        if not key:
            self.notify("No row selected", severity="warning")
            return
        bind = self._bind_for(key)
        remove_custom = bool(bind and bind.origin == Origin.CUSTOM)
        label = "Remove custom" if remove_custom else "Restore stock"
        msg = (
            f"Remove custom keybind [b]{key}[/b]?"
            if remove_custom
            else f"Restore [b]{key}[/b] to Archcraft default?"
        )

        def on_confirm(ok: bool | None) -> None:
            if not ok:
                return
            try:
                reset_one(key, path=self.rc_path, remove_custom=remove_custom)
            except (DefaultsError, KeyError) as exc:
                self.notify(str(exc), severity="error")
                return
            # Custom removed → stay near old index; otherwise reselect same key.
            if remove_custom:
                self.reload_data(select_row=self._active_table().cursor_row)
            else:
                self.reload_data(select_key=key)
            self._apply_live()
            self.notify(f"Reset {key}", severity="information")

        self.push_screen(ConfirmModal(msg, confirm_label=label), on_confirm)

    def action_reset_all(self) -> None:
        def on_confirm(ok: bool | None) -> None:
            if not ok:
                return
            info = reset_all(path=self.rc_path)
            self.reload_data()
            self._apply_live()
            backup = info.get("backup") or ""
            self.notify(
                f"Restored all keybinds from Archcraft defaults\n{backup}",
                severity="warning",
            )

        self.push_screen(
            ConfirmModal(
                "Replace the entire [b]<keyboard>[/b] section with\n"
                "Archcraft defaults from /etc/skel?\n\n"
                "Theme/mouse settings are kept. A backup will be created.",
                confirm_label="Reset all",
            ),
            on_confirm,
        )

    def action_apply(self) -> None:
        try:
            info = apply_changes(self.keybinds)
        except FileNotFoundError as exc:
            self.notify(str(exc), severity="error")
            return
        code = info["reconfigure_returncode"]
        if code == 0:
            self.notify("openbox --reconfigure OK", severity="information")
        else:
            err = info.get("reconfigure_stderr") or f"exit {code}"
            self.notify(f"Reconfigure failed: {err}", severity="error")


def run_tui(rc_path: Path | None = None) -> int:
    KeybinderApp(rc_path=rc_path).run()
    return 0
