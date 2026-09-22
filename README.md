# System Data Scanner

A lightweight macOS folder-size scanner built with Python and Tkinter. It shows the sizes of the immediate subfolders in a selected directory, sorted from largest to smallest.

## Features

- Scan `/Library` by default
- Enter any other folder path manually
- Choose a folder with the Browse button
- Display readable folder sizes
- Sort results by size, largest first
- Show scan progress and status updates
- Skip unreadable files and symbolic links

## Requirements

- macOS
- Python 3
- Tkinter

Tkinter is usually included with the official macOS Python installer. If your Python installation does not include it, install a Python distribution that provides Tk support.

## Run From Source

Clone the repository, open its directory, and run:

```bash
python3 main.py
```

Enter `/Library` or another directory in the Folder field, then click **Scan**.

## Build the macOS App

Install PyInstaller in your Python environment if needed:

```bash
python3 -m pip install pyinstaller
```

Build the application with the included spec file:

```bash
pyinstaller SystemDataScanner.spec
```

The generated application will be located at:

```text
dist/SystemDataScanner.app
```

## Permissions

macOS may restrict access to some system directories. If a folder cannot be scanned, grant the application or terminal access in **System Settings > Privacy & Security** and try again.

## License

No license has been specified yet.
