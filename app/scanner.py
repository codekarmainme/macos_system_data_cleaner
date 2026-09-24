import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def get_dir_size(path):
    """Calculate total size of a directory in bytes, skipping unreadable files."""
    total_size = 0
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    fp = os.path.join(root, file)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    return total_size


def format_size(bytes_size):
    """Convert bytes to human-readable string (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


class StorageScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("macOS System Data Scanner (/Library)")
        self.root.geometry("650x500")

        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Folder:").pack(side=tk.LEFT, padx=(0, 5))

        self.folder_var = tk.StringVar(value="/Library")
        self.folder_entry = ttk.Entry(control_frame, textvariable=self.folder_var)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = ttk.Button(control_frame, text="Browse", command=self.choose_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)

        self.scan_btn = ttk.Button(control_frame, text="Scan", command=self.start_scan_thread)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(
            self.root,
            text="Enter a folder and click 'Scan' to begin.",
            padding=(10, 0),
        )
        self.status_label.pack(fill=tk.X)

        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        chart_frame = ttk.Frame(self.root, padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.results_canvas = tk.Canvas(chart_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            chart_frame, orient=tk.VERTICAL, command=self.results_canvas.yview
        )
        self.results_canvas.configure(yscrollcommand=scrollbar.set)

        self.results_frame = ttk.Frame(self.results_canvas)
        self.results_window = self.results_canvas.create_window(
            (0, 0), window=self.results_frame, anchor="nw"
        )
        self.results_frame.bind(
            "<Configure>",
            lambda event: self.results_canvas.configure(
                scrollregion=self.results_canvas.bbox("all")
            ),
        )
        self.results_canvas.bind(
            "<Configure>",
            lambda event: self.results_canvas.itemconfigure(
                self.results_window, width=event.width
            ),
        )

        self.results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def start_scan_thread(self):
        """Run scanning in a background thread to keep GUI responsive."""
        target_dir = os.path.abspath(os.path.expanduser(self.folder_var.get().strip()))
        if not os.path.isdir(target_dir):
            messagebox.showerror("Invalid folder", "Please enter an existing folder.")
            return

        self.scan_btn.config(state=tk.DISABLED)
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.status_label.config(text=f"Scanning {target_dir}...")
        self.progress["value"] = 0

        thread = threading.Thread(
            target=self.scan_library, args=(target_dir,), daemon=True
        )
        thread.start()

    def choose_folder(self):
        selected_folder = filedialog.askdirectory(
            initialdir=self.folder_var.get() or "/"
        )
        if selected_folder:
            self.folder_var.set(selected_folder)

    def scan_library(self, target_dir):
        try:
            entries = [
                os.path.join(target_dir, name)
                for name in os.listdir(target_dir)
                if os.path.isdir(os.path.join(target_dir, name))
            ]
        except PermissionError:
            messagebox.showerror(
                "Error", f"Permission denied accessing {target_dir}"
            )
            self.scan_btn.config(state=tk.NORMAL)
            return

        total_folders = len(entries)
        results = []

        for index, path in enumerate(entries):
            folder_name = os.path.basename(path)
            self.status_label.config(text=f"Scanning: {folder_name}...")
            size = get_dir_size(path)
            results.append((folder_name, size, path))
            if total_folders:
                self.progress["value"] = ((index + 1) / total_folders) * 100

        results.sort(key=lambda item: item[1], reverse=True)
        self.display_results(results)
        self.status_label.config(text=f"Scan complete. Analyzed {total_folders} folders.")
        self.scan_btn.config(state=tk.NORMAL)

    def display_results(self, results):
        """Display each directory as a clickable proportional colored bar."""
        if not results:
            ttk.Label(self.results_frame, text="No subdirectories found.").pack(
                anchor=tk.W, pady=10
            )
            return

        largest_size = max(size for _, size, _ in results) or 1
        colors = ("#2563eb", "#0891b2", "#059669", "#ca8a04", "#dc2626")

        for index, (folder, size, path) in enumerate(results):
            row = ttk.Frame(self.results_frame, padding=(0, 4), cursor="hand2")
            row.pack(fill=tk.X)

            name_label = ttk.Label(row, text=folder, width=32, anchor=tk.W)
            name_label.pack(side=tk.LEFT)

            bar = tk.Canvas(row, height=22, background="#e5e7eb", highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
            color = colors[index % len(colors)]
            bar.bind(
                "<Configure>",
                lambda event, canvas=bar, value=size, maximum=largest_size, fill=color: self.draw_bar(
                    event, canvas, value, maximum, fill
                ),
            )

            size_label = ttk.Label(row, text=format_size(size), width=14, anchor=tk.E)
            size_label.pack(side=tk.RIGHT)

            for widget in (row, name_label, bar, size_label):
                widget.bind(
                    "<Button-1>",
                    lambda event, selected_path=path: self.show_directory_details(
                        selected_path
                    ),
                )

    @staticmethod
    def draw_bar(event, canvas, value, maximum, fill):
        canvas.delete("bar")
        canvas.create_rectangle(
            0,
            0,
            event.width * value / maximum,
            event.height,
            fill=fill,
            outline="",
            tags="bar",
        )

    def show_directory_details(self, path):
        """Open a detail view for the selected directory."""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Details: {os.path.basename(path)}")
        detail_window.geometry("700x500")

        ttk.Label(
            detail_window,
            text=path,
            padding=(10, 10),
        ).pack(fill=tk.X)

        detail_canvas = tk.Canvas(detail_window, highlightthickness=0)
        detail_scrollbar = ttk.Scrollbar(
            detail_window, orient=tk.VERTICAL, command=detail_canvas.yview
        )
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        detail_frame = ttk.Frame(detail_canvas, padding=10)
        detail_window_id = detail_canvas.create_window(
            (0, 0), window=detail_frame, anchor="nw"
        )
        detail_frame.bind(
            "<Configure>",
            lambda event: detail_canvas.configure(
                scrollregion=detail_canvas.bbox("all")
            ),
        )
        detail_canvas.bind(
            "<Configure>",
            lambda event: detail_canvas.itemconfigure(
                detail_window_id, width=event.width
            ),
        )
        detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        try:
            entries = []
            for name in os.listdir(path):
                entry_path = os.path.join(path, name)
                if os.path.isdir(entry_path):
                    entries.append((name, get_dir_size(entry_path), entry_path))
                elif os.path.isfile(entry_path):
                    try:
                        entries.append((name, os.path.getsize(entry_path), None))
                    except (PermissionError, FileNotFoundError):
                        continue
        except PermissionError:
            ttk.Label(detail_frame, text="Permission denied reading this directory.").pack(
                anchor=tk.W
            )
            return

        entries.sort(key=lambda item: item[1], reverse=True)
        if not entries:
            ttk.Label(detail_frame, text="This directory is empty.").pack(anchor=tk.W)
            return

        largest_size = max(size for _, size, _ in entries) or 1
        colors = ("#2563eb", "#0891b2", "#059669", "#ca8a04", "#dc2626")
        for index, (name, size, child_path) in enumerate(entries):
            row = ttk.Frame(detail_frame, padding=(0, 4))
            row.pack(fill=tk.X)
            ttk.Label(row, text=name, width=32, anchor=tk.W).pack(side=tk.LEFT)
            bar = tk.Canvas(row, height=22, background="#e5e7eb", highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
            color = colors[index % len(colors)]
            bar.bind(
                "<Configure>",
                lambda event, canvas=bar, value=size, maximum=largest_size, fill=color: self.draw_bar(
                    event, canvas, value, maximum, fill
                ),
            )
            ttk.Label(row, text=format_size(size), width=14, anchor=tk.E).pack(
                side=tk.RIGHT
            )
            if child_path:
                row.configure(cursor="hand2")
                row.bind(
                    "<Button-1>",
                    lambda event, selected_path=child_path: self.show_directory_details(
                        selected_path
                    ),
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = StorageScannerApp(root)
    root.mainloop()
