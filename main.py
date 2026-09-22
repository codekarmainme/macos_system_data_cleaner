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
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


class StorageScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("macOS System Data Scanner (/Library)")
        self.root.geometry("650x500")

        # Top Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Folder:").pack(side=tk.LEFT, padx=(0, 5), )

        self.folder_var = tk.StringVar(value="/Library")
        self.folder_entry = ttk.Entry(control_frame, textvariable=self.folder_var)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = ttk.Button(control_frame, text="Browse", command=self.choose_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)

        self.scan_btn = ttk.Button(control_frame, text="Scan", command=self.start_scan_thread)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(self.root, text="Enter a folder and click 'Scan' to begin.", padding=(10, 0))
        self.status_label.pack(fill=tk.X)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        # Table Frame (Treeview)
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("folder", "size", "raw_size")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
       
        self.tree.heading("folder", text="Directory")
        self.tree.heading("size", text="Size")
        self.tree.column("folder", width=420)
        self.tree.column("size", width=150, anchor=tk.E)
        self.tree.column("raw_size", width=0, stretch=tk.NO)  # Hidden for sorting

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def start_scan_thread(self):
        """Run scanning in a background thread to keep GUI responsive."""
        target_dir = os.path.abspath(os.path.expanduser(self.folder_var.get().strip()))
        if not os.path.isdir(target_dir):
            messagebox.showerror("Invalid folder", "Please enter an existing folder.")
            return

        self.scan_btn.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text=f"Scanning {target_dir}...")
        
        thread = threading.Thread(target=self.scan_library, args=(target_dir,), daemon=True)
        thread.start()

    def choose_folder(self):
        selected_folder = filedialog.askdirectory(initialdir=self.folder_var.get() or "/")
        if selected_folder:
            self.folder_var.set(selected_folder)

    def scan_library(self, target_dir):
        try:
            entries = [os.path.join(target_dir, d) for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
        except PermissionError:
            messagebox.showerror("Error", "Permission denied accessing /Library")
            self.scan_btn.config(state=tk.NORMAL)
            return

        total_folders = len(entries)
        results = []

        for i, path in enumerate(entries):
            folder_name = os.path.basename(path)
            self.status_label.config(text=f"Scanning: {folder_name}...")
            
            size = get_dir_size(path)
            results.append((folder_name, size))
            
            # Update Progress Bar
            self.progress['value'] = ((i + 1) / total_folders) * 100

        # Sort by size descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Populate UI Treeview
        for folder, size in results:
            self.tree.insert("", tk.END, values=(folder, format_size(size), size))

        self.status_label.config(text=f"Scan complete. Analyzed {total_folders} folders.")
        self.scan_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = StorageScannerApp(root)
    root.mainloop()