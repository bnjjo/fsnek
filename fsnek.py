from icons import ICONS
from typing import Literal
from pathlib import Path
from datetime import datetime
from send2trash import send2trash as trash
from textual.app import App, ComposeResult
from textual.events import Key
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Input, Static
from textual.containers import Container
from textual.coordinate import Coordinate


class FileTable(DataTable):
    HOME_DIR = Path.home()
    BINDINGS = [
        Binding("h",         "cursor_left",          "scroll left",                    show=False),
        Binding("j",         "cursor_down",          "go down",                        show=True),
        Binding("k",         "cursor_up",            "go up",                          show=True),
        Binding("l",         "cursor_right",         "scroll right",                   show=False),
        Binding("enter",     "select_cursor",        "open",                           show=True),
        Binding("backspace", "go_back",              "back",                           show=True),
        Binding("minus",     "go_back",              "back",                           show=False),
        Binding("g",         "scroll_top",           "top",                            show=False),
        Binding("G",         "scroll_bottom",        "bottom",                         show=False),
        Binding("ctrl+u",    "half_page_up",         "half page up",                   show=False),
        Binding("ctrl+d",    "half_page_down",       "half page down",                 show=False),
        Binding("v/V",       "toggle_visual_mode",   "visual",                         show=True),
        Binding("v",         "toggle_visual_mode",   "visual",                         show=False),
        Binding("V",         "toggle_visual_mode",   "visual-line",                    show=False),
        Binding("escape",    "escape_pressed",       "escape visual/visual-line mode", show=False),
        Binding("a",         "rename(False, False)", "append",                         show=True),
        Binding("A",         "rename(False, True)",  "append",                         show=False),
        Binding("i",         "rename(True, False)",  "insert",                         show=True),
        Binding("I",         "rename(True, False)",  "insert",                         show=False),
        Binding("o/O",       "create_file",          "create file",                    show=True),
        Binding("o",         "create_file",          "create file",                    show=False),
        Binding("O",         "create_file",          "create file",                    show=False),
        Binding("yy",        "yank",                 "yank",                           show=True),
        Binding("y",         "yank",                 "yank",                           show=False),
        Binding("dd",        "delete",               "delete",                         show=True),
        Binding("d",         "delete",               "delete",                         show=False),
    ]
    MAX_COLUMN_WIDTH = 20

    current_path = Path(HOME_DIR)
    last_cursor_positions = []

    current_rows = 0
    current_row_idx = 0
    current_row_key = 0
    selected_row_keys = []
    deletion_queue = []

    visual_mode = False
    visual_start_row = 0
    visual_end_row = 0

    tap_count = 0

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True

        # COLUMNS
        self.add_column("")
        self.add_column("Name", width=self.MAX_COLUMN_WIDTH)
        self.add_column("Size", width=7) # 7 character max width e.g. 1023.4K
        self.add_column("Last Modified")

        self.render()

    def render(self) -> None:
        self.current_rows = 0

        def assign_icon(path: Path) -> str:
            if path.is_dir():
                return ICONS["directory"]

            extension = path.suffix[1:].lower()
            return ICONS.get(extension, ICONS["generic_file"])

        def human_readable_size(size: float, decimal_places: int = 1):
            for unit in ['B', 'K', 'M', 'G', 'T', 'P']:
                if size < 1024.0 and unit == 'B':
                    return f"{size}{unit}"
                if size < 1024.0 or unit == 'P':
                    break
                size /= 1024.0
            return f"{size:.{decimal_places}f}{unit}"

        def add_to_filetable(item: Path) -> None:
            try:
                stat_info = item.stat()
                lm_timestamp = stat_info.st_mtime
                lm_time = datetime.fromtimestamp(lm_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                size = human_readable_size(stat_info.st_size)

                # TODO: add elipses for when file names are too long

                # name_limit = self.MAX_COLUMN_WIDTH - 3
                # if len(item.name) > name_limit:
                #     formatted_name = f"{item.name[:name_limit]}..."
                # else:
                #     formatted_name = item.name

                if Path(f"{self.current_path}/{item.name}") not in self.deletion_queue:
                    self.add_row(
                        assign_icon(item),
                        item.name,
                        size,
                        lm_time,
                    )

                self.current_rows += 1

            except FileNotFoundError:
                self.add_row(assign_icon(item), item.name, "Unknown", "Unknown")

        self.clear()

        files = []
        directories = []
        all_items = []

        for directory in self.current_path.iterdir():
            if directory.name[0] != "." and directory.is_dir():
                directories.append(directory)
        for file in self.current_path.iterdir():
            if file.name[0] != "." and not file.is_dir():
                files.append(file)

        all_items = sorted(directories) + sorted(files)
        for item in all_items:
            add_to_filetable(item)

        self.deletion_queue.clear()

    def _should_highlight(
        self,
        cursor: Coordinate,
        target_cell: Coordinate,
        type_of_cursor=Literal["cell", "row", "column", "none"],
    ) -> bool:
        if self.visual_mode:
            target_row, _ = target_cell
            start = min(self.visual_start_row, self.visual_end_row)
            end = max(self.visual_start_row, self.visual_end_row)
            if start <= target_row <= end:
                return True
        
        return super()._should_highlight(cursor, target_cell, type_of_cursor)

    def watch_cursor_coordinate(self, old: Coordinate, new: Coordinate) -> None:
        super().watch_cursor_coordinate(old, new)
        if self.visual_mode:
            self.visual_end_row = new.row
            self.refresh()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_row_keys.clear()
        selected_row = self.get_row_at(event.cursor_row)[1]
        new_path = Path(f"{self.current_path}/{selected_row}")
        previous_path = self.current_path
        if new_path.is_dir():
            try:
                self.current_path = new_path
                self.last_cursor_positions.append(event.cursor_row)
                self.render()
            except PermissionError:
                self.current_path = previous_path
                self.notify("Cannot access directory: Permission denied", severity="error", timeout=5)
                self.render()
                self.move_cursor(row=self.last_cursor_positions[-1])
                self.last_cursor_positions.pop()
            else:
                self.turn_visual_mode_off()
        else:
            self.notify("Cannot open file: No default application set for opening this type of file", severity="error", timeout=5)

    def on_data_table_row_highlighted(self, event: DataTable.RowSelected) -> None:
        self.current_row_idx = event.cursor_row
        self.current_row_key = event.row_key

    def action_go_back(self) -> None:
        self.selected_row_keys.clear()
        new_path = Path(f"{self.current_path.parent.absolute()}")
        if self.current_path != self.HOME_DIR:
            self.current_path = new_path
            self.turn_visual_mode_off()
            self.render()
            self.move_cursor(row=self.last_cursor_positions[-1])
            self.last_cursor_positions.pop()
        else:
            self.notify("Error: Cannot go back any further", severity="error", timeout=5)

    def action_toggle_visual_mode(self) -> None:
        if not self.visual_mode:
            self.visual_mode = True
            self.visual_start_row = self.cursor_row
            self.visual_end_row = self.cursor_row
            self.selected_row_keys.append(self.current_row_key)
            self.add_class("visual-mode")
            status = "on"
        else:
            self.turn_visual_mode_off()
            status = "off"
        
        self.refresh()

    def turn_visual_mode_off(self) -> None:
        self.visual_mode = False
        self.remove_class("visual-mode")

    def is_double_tap(self) -> bool:
        self.tap_count += 1
        
        if self.tap_count == 1:
            self.set_timer(0.5, lambda: setattr(self, 'tap_count', 0))
            return False
        elif self.tap_count == 2:
            self.tap_count = 0
            return True

    def action_scroll_top(self) -> None:
        if self.is_double_tap():
            self.move_cursor(row=0)

    def action_half_page_up(self) -> None:
        self._set_hover_cursor(False)
        if self.show_cursor and self.cursor_type in ("cell", "row"):
            visible_height = self.scrollable_content_region.height - (
                self.header_height if self.show_header else 0
            )
            half_height = visible_height // 2
            row_index, _ = self.cursor_coordinate
            
            target_row = max(0, row_index - (visible_height // 2))
            
            self.scroll_relative(y=-half_height, animate=False)
            self.move_cursor(row=target_row, scroll=True)
        else:
            visible_height = self.scrollable_content_region.height
            self.scroll_relative(y=-(visible_height // 2), animate=False)

    def action_half_page_down(self) -> None:
        self._set_hover_cursor(False)
        if self.show_cursor and self.cursor_type in ("cell", "row"):
            visible_height = self.scrollable_content_region.height - (
                self.header_height if self.show_header else 0
            )
            half_height = visible_height // 2
            row_index, _ = self.cursor_coordinate
            
            max_row = len(self.ordered_rows) - 1
            target_row = min(max_row, row_index + (visible_height // 2))
            
            self.scroll_relative(y=half_height, animate=False)
            self.move_cursor(row=target_row, scroll=True)
        else:
            visible_height = self.scrollable_content_region.height
            self.scroll_relative(y=(visible_height // 2), animate=False)

    def action_yank(self) -> None:
        timeout = 0.2

        if self.visual_mode:
            self.add_class("yanking-it")
            self.set_timer(timeout, lambda: self.remove_class("yanking-it"))
            self.set_timer(timeout, lambda: self.turn_visual_mode_off())
        elif self.is_double_tap():
            self.add_class("yanking-it")
            self.set_timer(timeout, lambda: self.remove_class("yanking-it"))

    def action_delete(self) -> None:
        if self.visual_mode:
            if self.current_row_key not in self.selected_row_keys:
                self.selected_row_keys.append(self.current_row_key)
            if self.visual_start_row < self.visual_end_row:
                start = self.visual_start_row
                end = self.visual_end_row
            else:
                start = self.visual_end_row
                end = self.visual_start_row

            for row_idx in range(start, end):
                if self.ordered_rows[row_idx].key not in self.selected_row_keys:
                    self.selected_row_keys.append(self.ordered_rows[row_idx].key)

            for row_key in self.selected_row_keys:
                self.deletion_queue.append(Path(f"{self.current_path}/{self.get_row(row_key)[1]}"))
                self.remove_row(row_key)

            self.turn_visual_mode_off()
            self.selected_row_keys.clear()
            self.tap_count = 0
            self.show_dialog("DELETE")
    
        if self.is_double_tap() and not self.visual_mode:
            self.deletion_queue.append(Path(f"{self.current_path}/{self.get_row(self.current_row_key)[1]}"))
            self.remove_row(self.current_row_key)
            self.show_dialog("DELETE")

    def action_escape_pressed(self) -> None:
        if self.visual_mode:
            self.turn_visual_mode_off()

    def show_dialog(self, command: str) -> None:
        overlay = self.app.query_one(Overlay)
        overlay.styles.display = "block"
        dialog = self.app.query_one(DialogBox)
        dialog.styles.display = "block"

        if command == "DELETE":
            output = ""
            pending_actions = ""
            for item in self.deletion_queue:
                # todo: change this from a dollar sign
                # it will lead to improper splitting on mac
                # if a dir name contains a dollar sign
                pending_actions = pending_actions + str(item) + "$"
                output = output + f"DELETE: {str(item)}\n"

        dialog.actions = pending_actions[:-1]
        dialog.update(f"Would you like to:\n{output}\n\[Y]es        \[N]o")
        dialog.focus()

    def action_rename(self, insert: bool = False, append_at_end: bool = False) -> None:
        if self.current_rows < 1:
            self.notify("Nothing to rename", severity="error", timeout=5)
        else:
            overlay = self.app.query_one(Overlay)
            overlay.styles.display = "block"
            input_box = self.app.query_one(InputBox)
            input_box.styles.display = "block"
            input = input_box.query_one(Input)
            file_name = self.get_row(self.current_row_key)[1]
            input.value = file_name
            if insert:
                input.cursor_position = 0
            elif "." in file_name:
                if append_at_end:
                    input.cursor_position = len(file_name)
                else:
                    input.cursor_position = len(file_name.split(".")[0])
            else: 
                input.cursor_position = len(file_name)
            input.focus()


class Overlay(Container):
    DEFAULT_CSS = """
    Overlay {
        width: 100%;
        height: 99%;
        align: center middle;
        display: none;
    }
    """


class DialogBox(Static, can_focus=True):
    BINDINGS = [
        ("y", "confirm", "confirm"),
        ("n", "abort", "abort"),
    ]
    DEFAULT_CSS = """
    DialogBox {
        width: 90%;
        height: auto;
        padding: 1 2;
        background: $panel;
        border: tall $primary;
        content-align: center middle;
        text-align: center;
        display: none;
    }
    """

    actions = ""
    command = ""

    def action_confirm(self) -> None:
        overlay = self.app.query_one(Overlay)
        overlay.styles.display = "none"
        file_table = self.app.query_one(FileTable)

        if self.command == "DELETE":
            self.delete_files()

        self.actions = ""
        self.command = ""
        file_table.focus()

    def action_abort(self) -> None:
        overlay = self.app.query_one(Overlay)
        overlay.styles.display = "none"
        file_table = self.app.query_one(FileTable)
        self.actions = ""
        self.command = ""
        file_table.deletion_queue.clear()
        file_table.render()
        file_table.move_cursor(row=file_table.current_row_idx)
        file_table.focus()

    def delete_files(self) -> None:
        self.actions = self.actions.split("$")
        for i in self.actions:
            trash(i)


class InputBox(Static, can_focus=True):
    BINDINGS = [
        ("escape", "exit", "cancel"),
    ]
    DEFAULT_CSS = """
    InputBox {
        max-width: 50;
        content-align: center middle;
        text-align: center;
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(select_on_focus=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        file_table = self.app.query_one(FileTable)
        old_path = Path(f"{file_table.current_path}/{file_table.get_row(file_table.current_row_key)[1]}")
        if event.value == "":
            self.notify("Name cannot be empty", severity="error", timeout=5)
        else:
            new_path = old_path.with_name(event.value)
            old_path.rename(new_path)
        self.action_exit()

    def action_exit(self) -> None:
        overlay = self.app.query_one(Overlay)
        overlay.styles.display = "none"
        self.styles.display = "none"
        file_table = self.app.query_one(FileTable)
        file_table.render()
        file_table.move_cursor(row=file_table.current_row_idx)
        file_table.focus()


class FsnekApp(App):
    BINDINGS = [
        ("q", "quit", "quit"),
    ]
    CSS = """
    Screen {
        layers: base overlay;
    }
    
    FileTable, Footer {
        layer: base;
    }
    
    Overlay {
        layer: overlay;
        background: $background 30%;
    }
    
    DataTable > .datatable--cursor {
        background: #88C0D0;
    }
    
    DataTable.visual-mode > .datatable--cursor {
        background: #C4A7E7;
    }

    DataTable.yanking-it > .datatable--cursor {
        background: #F6C177;
    }
    """
    config_file = Path("config")
    selected_theme = "textual-dark"

    def compose(self) -> ComposeResult:
        yield FileTable()
        yield Footer()
        with Overlay():
            yield DialogBox()
            yield InputBox()

    def on_mount(self) -> None:
        if self.config_file.exists():
            self.theme = self.config_file.read_text().strip()
        else:
            self.theme = self.selected_theme

    def on_key(self, event: Key) -> None:
        if event.key == "q":
            self.selected_theme = self.theme
            self.config_file.write_text(self.selected_theme)


if __name__ == "__main__":
    app = FsnekApp()
    app.run()
