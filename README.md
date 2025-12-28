<p align="center">
  <img width="2560" height="1407" alt="image" src="https://github.com/user-attachments/assets/162dafc3-0279-417f-8a9a-1ddfc4c08cfd" />
</p>

# fsnek

A Vim-inspired TUI file manager built with Python and Textual.

## Features

- Vim-style keybindings for navigation and file operations
- Visual mode for selecting multiple files
- File operations: create, rename, move, copy, delete
- Automatic image copying to clipboard when yanking image files
- Trash integration for safe file deletion
- Theme customization with persistent settings
- Directory and file icons

## Requirements

- Python 3.10 or higher

## Installation

Create and activate a virtual environment, then install fsnek:

```
pip install git+https://github.com/bnjjo/fsnek.git
```

With your virtual environment activated, you can run fsnek from anywhere:

```
fsnek [optional/path/to/directory]
```

**Note:** The `fsnek` command will only be available when your virtual environment is activated. Alternatively, you can install with `pipx` for global access without needing to activate a virtual environment:

```
pipx install git+https://github.com/bnjjo/fsnek.git
```

## Keybindings

### Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `h` | Scroll left | Scroll table view left |
| `j` | Move down | Move cursor down one row |
| `k` | Move up | Move cursor up one row |
| `l` | Scroll right | Scroll table view right |
| `gg` (double tap `g`) | Go to top | Jump to first item |
| `G` | Go to bottom | Jump to last item |
| `Ctrl+u` | Half page up | Scroll up by half a page |
| `Ctrl+d` | Half page down | Scroll down by half a page |
| `Enter` | Open | Open directory or file |
| `Backspace` or `-` | Go back | Navigate to parent directory |

### Visual Mode

| Key | Action | Description |
|-----|--------|-------------|
| `v` | Visual mode | Enter visual mode to select multiple files |
| `V` | Visual line mode | Enter visual line mode |
| `y` | Yank selection | Copy all selected files |
| `x` | Move selection | Cut all selected files for moving |
| `d` | Delete selection | Move all selected files to trash |
| `Escape` | Exit visual mode | Cancel selection and return to normal mode |

### File Operations

| Key | Action | Description |
|-----|--------|-------------|
| `a` | Append | Rename file, cursor at end of name (before extension) |
| `A` | Append at end | Rename file, cursor at very end of name |
| `i` or `I` | Insert | Rename file, cursor at beginning of name |
| `o` or `O` | Create file | Create new file (add `/` at end for directory) |
| `dd` (double tap `d`) | Delete | Move selected file(s) to trash |
| `xx` (double tap `x`) | Move | Cut file(s) for moving |
| `yy` (double tap `y`) | Yank | Copy file(s) to clipboard |
| `p` | Put | Paste copied or cut files to current directory |

### Application

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit fsnek |
| `Escape` | Cancel | Cancel current operation or exit visual mode |

## Configuration

fsnek stores its theme configuration in `~/.config/fsnek/config`. The selected theme persists across sessions.

## Dependencies

- **Textual** (6.11.0): TUI framework
- **Pillow** (11.3.0): Image processing for clipboard operations
- **pyperclipimg** (0.2.0): Clipboard image support
- **Send2Trash** (1.8.3): Safe file deletion

## License

MIT
