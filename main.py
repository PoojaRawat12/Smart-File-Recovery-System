import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
from datetime import datetime

# Try to import winshell safely
try:
    import winshell
    winshell_available = True
except ImportError:
    winshell_available = False
    print("winshell module not found. Recycle Bin features disabled.")

# Constants
deleted_folder = "DeletedFile"
recovered_folder = "RecoveredFile"
delete_log_file = "log.json"
restore_log_file = "restore_log.json"
os.makedirs(deleted_folder, exist_ok=True)
os.makedirs(recovered_folder, exist_ok=True)

# --- Logging Functions ---
def read_delete_log():
    if os.path.exists(delete_log_file):
        with open(delete_log_file, 'r') as f:
            return json.load(f)
    return {}

def write_delete_log(log):
    with open(delete_log_file, 'w') as f:
        json.dump(log, f, indent=4)

def read_restore_history():
    if os.path.exists(restore_log_file):
        with open(restore_log_file, 'r') as f:
            return json.load(f)
    return []

def write_restore_history(history):
    with open(restore_log_file, 'w') as f:
        json.dump(history, f, indent=4)

# --- Delete File ---
def select_and_delete_file():
    file_path = filedialog.askopenfilename(title="Select file to delete")
    if not file_path:
        messagebox.showwarning("No File Selected", "You didn't select any file.")
        return

    if not os.path.isfile(file_path):
        messagebox.showerror("Invalid Selection", "Please select a valid file (not a folder).")
        return

    file_name = os.path.basename(file_path)
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{file_name}'?")
    if not confirm:
        return

    try:
        shutil.move(file_path, os.path.join(deleted_folder, file_name))
        log = read_delete_log()
        log[file_name] = file_path
        write_delete_log(log)
        refresh_file_lists()
        messagebox.showinfo("Deleted", f"'{file_name}' has been deleted successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete '{file_name}':\n{e}")

# --- Delete Folder ---
def select_and_delete_folder():
    folder_path = filedialog.askdirectory(title="Select folder to delete")
    if not folder_path:
        messagebox.showwarning("No Folder Selected", "You didn't select any folder.")
        return

    if not os.path.isdir(folder_path):
        messagebox.showerror("Invalid Selection", "Please select a valid folder.")
        return

    folder_name = os.path.basename(folder_path)
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the folder '{folder_name}'?")
    if not confirm:
        return

    try:
        dest = os.path.join(deleted_folder, folder_name)
        shutil.move(folder_path, dest)
        log = read_delete_log()
        log[folder_name] = folder_path
        write_delete_log(log)
        refresh_file_lists()
        messagebox.showinfo("Deleted", f"Folder '{folder_name}' has been deleted successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete folder '{folder_name}':\n{e}")

# --- Restore File ---
def select_and_restore_file():
    selected = deleted_listbox.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a file or folder to restore.")
        return
    file_name = deleted_listbox.get(selected[0])
    log = read_delete_log()
    original_path = log.get(file_name)

    if not original_path:
        messagebox.showerror("Not Found", f"Original path for '{file_name}' not found.")
        return

    confirm = messagebox.askyesno("Confirm Restore", f"Restore '{file_name}' to:\n{original_path}?")
    if not confirm:
        return

    try:
        shutil.move(os.path.join(deleted_folder, file_name), original_path)

        # ✅ ADDED: Copy restored file to recovered_folder for display
        if os.path.isfile(original_path):
            shutil.copy(original_path, os.path.join(recovered_folder, file_name))

        log.pop(file_name)
        write_delete_log(log)

        history = read_restore_history()
        history.append({
            "file_name": file_name,
            "original_path": original_path,
            "restored_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        write_restore_history(history)
        refresh_file_lists()
        messagebox.showinfo("Restored", f"'{file_name}' has been restored successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Restore failed: {e}")

# --- Recycle Bin Functions ---
def get_deleted_recyclebin_files():
    items = []
    if not winshell_available:
        return items
    for item in winshell.recycle_bin():
        try:
            name = str(item.filename() if callable(item.filename) else item.filename)
            path = str(item.original_filename() if callable(item.original_filename) else item.original_filename)
            items.append((name, path))
        except Exception as e:
            print("Error reading recycle bin item:", e)
    return items

def search_recyclebin_files(*args):
    query = recycle_search_var.get().lower()
    recycle_listbox.delete(0, tk.END)
    for file, path in recycle_files:
        if query in file.lower() or query in path.lower():
            recycle_listbox.insert(tk.END, f"{file} -> {path}")

def refresh_recycle_list():
    global recycle_files
    recycle_files = get_deleted_recyclebin_files()
    search_recyclebin_files()

def restore_recycle_file():
    if not winshell_available:
        messagebox.showerror("Not Available", "winshell module not available.")
        return
    selected = recycle_listbox.curselection()
    if selected:
        file_name = recycle_listbox.get(selected[0]).split(" -> ")[0]
        file_path = None
        for file, path in recycle_files:
            if file == file_name:
                file_path = path
                break
        if file_path:
            confirm = messagebox.askyesno("Confirm Restore", f"Restore '{file_name}' from Recycle Bin?")
            if not confirm:
                return
            try:
                winshell.undelete(file_path)
                messagebox.showinfo("Restored", f"Restored '{file_name}' from Recycle Bin")
                refresh_recycle_list()
            except Exception as e:
                messagebox.showerror("Error", f"Restore failed: {e}")

# --- UI Logic ---
def refresh_file_lists(filtered=None):
    deleted_listbox.delete(0, tk.END)
    recovered_listbox.delete(0, tk.END)
    files = os.listdir(deleted_folder)
    if filtered:
        files = [f for f in files if filtered.lower() in f.lower()]
    for f in files:
        deleted_listbox.insert(tk.END, f)
    for f in os.listdir(recovered_folder):
        recovered_listbox.insert(tk.END, f)

def show_restore_history_window():
    history = read_restore_history()
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

def search_deleted_files():
    query = search_var.get()
    refresh_file_lists(filtered=query)

def search_recovered_files(query):
    recovered_listbox.delete(0, tk.END)
    files = os.listdir(recovered_folder)
    for f in files:
        if query.lower() in f.lower():
            recovered_listbox.insert(tk.END, f)

def toggle_theme():
    global is_dark_mode
    is_dark_mode = not is_dark_mode
    apply_theme()

def apply_theme():
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

# --- GUI Setup ---
root = tk.Tk()
root.title("File Recovery Tool")
root.geometry("950x700")

style = ttk.Style()
is_dark_mode = False
apply_theme()

# --- Top Buttons ---
top_frame = ttk.Frame(root)
top_frame.pack(pady=10)

ttk.Button(top_frame, text="Delete File", command=select_and_delete_file, width=20).grid(row=0, column=0, padx=5)
ttk.Button(top_frame, text="Delete Folder", command=select_and_delete_folder, width=20).grid(row=0, column=1, padx=5)
ttk.Button(top_frame, text="Recover File", command=select_and_restore_file, width=20).grid(row=0, column=2, padx=5)
ttk.Button(top_frame, text="View Restore History", command=show_restore_history_window, width=20).grid(row=0, column=3, padx=5)
ttk.Button(top_frame, text="Toggle Dark Mode", command=toggle_theme, width=20).grid(row=0, column=4, padx=5)

# --- Search ---
search_frame = ttk.Frame(root)
search_frame.pack(pady=5)

ttk.Label(search_frame, text="Search Deleted Files:").pack(side=tk.LEFT, padx=5)
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
search_entry.pack(side=tk.LEFT, padx=5)
ttk.Button(search_frame, text="Search", command=search_deleted_files).pack(side=tk.LEFT, padx=5)

ttk.Label(search_frame, text="Search Recovered Files:").pack(side=tk.LEFT, padx=(30, 5))
search_recovered_var = tk.StringVar()
search_recovered_entry = ttk.Entry(search_frame, textvariable=search_recovered_var, width=30)
search_recovered_entry.pack(side=tk.LEFT, padx=5)
search_recovered_var.trace("w", lambda *args: search_recovered_files(search_recovered_var.get()))

# --- File Lists ---
list_frame = ttk.Frame(root)
list_frame.pack(pady=20)

ttk.Label(list_frame, text="Deleted Files").grid(row=0, column=0, padx=30)
ttk.Label(list_frame, text="Recovered Files").grid(row=0, column=1, padx=30)

deleted_listbox = tk.Listbox(list_frame, width=40, height=10)
deleted_listbox.grid(row=1, column=0, padx=20)

recovered_listbox = tk.Listbox(list_frame, width=40, height=10)
recovered_listbox.grid(row=1, column=1, padx=20)

# --- Recycle Bin View ---
if winshell_available:
    ttk.Label(root, text="Recycle Bin Files").pack(pady=(10, 0))
    recycle_search_var = tk.StringVar()
    recycle_search_var.trace("w", search_recyclebin_files)
    recycle_search_entry = ttk.Entry(root, textvariable=recycle_search_var, width=50)
    recycle_search_entry.pack(pady=5)

    recycle_listbox = tk.Listbox(root, width=100, height=10)
    recycle_listbox.pack()

    recycle_btn_frame = ttk.Frame(root)
    recycle_btn_frame.pack(pady=5)

    ttk.Button(recycle_btn_frame, text="Refresh Recycle Bin", command=refresh_recycle_list).pack(side=tk.LEFT, padx=10)
    ttk.Button(recycle_btn_frame, text="Restore Selected", command=restore_recycle_file).pack(side=tk.LEFT, padx=10)

    recycle_files = get_deleted_recyclebin_files()
    search_recyclebin_files()

# --- Final Init ---
refresh_file_lists()
root.mainloop()
