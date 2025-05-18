import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
from datetime import datetime

# Constants
deleted_folder = "DeletedFile"
recovered_folder = "RecoveredFile"
log_file = "log.json"
restore_log_file = "restore_log.json"
os.makedirs(deleted_folder, exist_ok=True)
os.makedirs(recovered_folder, exist_ok=True)

# Load/save log and history
def load_log():
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return json.load(f)
    return {}

def save_log(log):
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=4)

def load_restore_log():
    if os.path.exists(restore_log_file):
        with open(restore_log_file, 'r') as f:
            return json.load(f)
    return []

def save_restore_log(history):
    with open(restore_log_file, 'w') as f:
        json.dump(history, f, indent=4)

# File Operations
def delete_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_name = os.path.basename(file_path)
        shutil.move(file_path, os.path.join(deleted_folder, file_name))
        log = load_log()
        log[file_name] = file_path
        save_log(log)
        update_file_lists()
        messagebox.showinfo("Success", f"Deleted {file_name}")

def recover_file():
    selected = deleted_listbox.curselection()
    if selected:
        file_name = deleted_listbox.get(selected[0])
        log = load_log()
        if file_name in log:
            original_path = log[file_name]
            source_path = os.path.join(deleted_folder, file_name)
            shutil.copy2(source_path, original_path)
            shutil.copy2(source_path, os.path.join(recovered_folder, file_name))
            os.remove(source_path)
            del log[file_name]
            save_log(log)

            # Save restore log
            restore_history = load_restore_log()
            restore_history.append({
                "file_name": file_name,
                "original_path": original_path,
                "restored_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_restore_log(restore_history)

            update_file_lists()
            messagebox.showinfo("Recovered", f"Recovered {file_name} to original location")

# Update File Lists
def update_file_lists(filtered=None):
    deleted_listbox.delete(0, tk.END)
    recovered_listbox.delete(0, tk.END)
    files = os.listdir(deleted_folder)
    if filtered:
        files = [f for f in files if filtered.lower() in f.lower()]
    for f in files:
        deleted_listbox.insert(tk.END, f)
    for f in os.listdir(recovered_folder):
        recovered_listbox.insert(tk.END, f)

# Restore History Window
def view_restore_history():
    history = load_restore_log()
    win = tk.Toplevel(root)
    win.title("Restore History")
    win.geometry("600x300")

    tree = ttk.Treeview(win, columns=("File", "Original Path", "Restored On"), show="headings")
    tree.heading("File", text="File Name")
    tree.heading("Original Path", text="Original Path")
    tree.heading("Restored On", text="Restored On")

    for entry in history:
        tree.insert("", tk.END, values=(entry["file_name"], entry["original_path"], entry["restored_on"]))

    tree.pack(fill=tk.BOTH, expand=True)
    scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Search Functionality
def search_files():
    query = search_var.get()
    update_file_lists(filtered=query)

# Theme toggle
def toggle_theme():
    global is_dark_mode
    is_dark_mode = not is_dark_mode
    set_theme()

def set_theme():
    if is_dark_mode:
        style.theme_use('clam')
        root.configure(bg="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TButton", background="#444", foreground="white")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TEntry", fieldbackground="#444", foreground="white")
    else:
        style.theme_use('default')
        root.configure(bg="SystemButtonFace")
        style.configure("TLabel", background="SystemButtonFace", foreground="black")
        style.configure("TButton", background="SystemButtonFace", foreground="black")
        style.configure("TFrame", background="SystemButtonFace")
        style.configure("TEntry", fieldbackground="white", foreground="black")

# Main GUI
root = tk.Tk()
root.title("File Recovery Tool")
root.geometry("850x550")

style = ttk.Style()
is_dark_mode = False
set_theme()

# --- Top Controls ---
top_frame = ttk.Frame(root)
top_frame.pack(pady=10)

ttk.Button(top_frame, text="Delete File", command=delete_file, width=20).grid(row=0, column=0, padx=5)
ttk.Button(top_frame, text="Recover File", command=recover_file, width=20).grid(row=0, column=1, padx=5)
ttk.Button(top_frame, text="View Restore History", command=view_restore_history, width=20).grid(row=0, column=2, padx=5)
ttk.Button(top_frame, text="Toggle Dark Mode", command=toggle_theme, width=20).grid(row=0, column=3, padx=5)

# --- Search Bar ---
search_frame = ttk.Frame(root)
search_frame.pack(pady=5)

ttk.Label(search_frame, text="Search Deleted Files:").pack(side=tk.LEFT, padx=5)
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
search_entry.pack(side=tk.LEFT, padx=5)
ttk.Button(search_frame, text="Search", command=search_files).pack(side=tk.LEFT, padx=5)

# --- File Display ---
list_frame = ttk.Frame(root)
list_frame.pack(pady=20)

ttk.Label(list_frame, text="Deleted Files").grid(row=0, column=0, padx=30)
ttk.Label(list_frame, text="Recovered Files").grid(row=0, column=1, padx=30)

deleted_listbox = tk.Listbox(list_frame, width=40, height=15)
deleted_listbox.grid(row=1, column=0, padx=20)

recovered_listbox = tk.Listbox(list_frame, width=40, height=15)
recovered_listbox.grid(row=1, column=1, padx=20)

update_file_lists()
root.mainloop()
