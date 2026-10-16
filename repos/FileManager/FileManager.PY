import os
import shutil
import sys
import string
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import time

class GUIFileManager(tk.Tk):
    """
    A sleek and functional graphical file manager with a directory tree,
    a sortable file view, search, drag-and-drop functionality, and an undo feature.
    All file operations are now performed directly in the main thread.
    """
    def __init__(self):
        super().__init__()
        self.title("Sleek File Manager")
        self.geometry("800x600")

        # --- AESTHETIC ENHANCEMENTS (Sleek Dark Theme) ---
        self.configure(bg="#212121")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure('TFrame', background='#212121')
        style.configure('TLabelFrame', background='#212121', foreground='#e0e0e0', font=('Arial', 10, 'bold'))
        style.configure('TLabel', background='#212121', foreground='#e0e0e0')
        style.configure('TButton', font=('Arial', 10), padding=8, background='#424242', foreground='#e0e0e0')
        style.map('TButton',
                  background=[('active', '#616161'), ('pressed', '#757575')],
                  foreground=[('active', '#ffffff')])
        style.configure('Treeview', background='#323232', foreground='#e0e0e0', fieldbackground='#323232', font=('Arial', 10), rowheight=24)
        style.map('Treeview',
                  background=[('selected', '#39796b')],
                  foreground=[('selected', '#ffffff')])
        
        # Store the current directory, starting at the user's home folder
        self.current_path = os.path.expanduser('~')
        self.clipboard = [] # For copy/paste functionality
        
        # Drag and drop state
        self.drag_start_item = None
        
        # --- UNDO FUNCTIONALITY ---
        self.undo_stack = []
        self.recycle_bin_dir = os.path.join(os.path.expanduser('~'), ".file_manager_recycle")
        os.makedirs(self.recycle_bin_dir, exist_ok=True)
        
        # --- SORTING STATE ---
        self.sort_column = 'modified'
        self.sort_reverse = True

        # --- LAYOUT FOR IMPROVED STRUCTURE ---
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.main_frame.grid_columnconfigure(0, weight=1)  # Left panel (tree)
        self.main_frame.grid_columnconfigure(1, weight=3)  # Right panel (file view)
        self.main_frame.grid_rowconfigure(1, weight=1)    # Main panels

        # Path label
        self.path_label = ttk.Label(self.main_frame, text=f"Current Path: {self.current_path}", font=('Arial', 10, 'bold'))
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Left Panel (Shortcuts, Drives, Tree) - now in column 0
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.grid(row=1, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=0)
        self.left_panel.grid_rowconfigure(1, weight=0)
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.shortcuts_frame = ttk.LabelFrame(self.left_panel, text="Shortcuts")
        self.shortcuts_frame.grid(row=0, column=0, sticky="ew")

        self.drives_frame = ttk.LabelFrame(self.left_panel, text="Drives")
        self.drives_frame.grid(row=1, column=0, sticky="ew")

        self.tree_frame = ttk.Frame(self.left_panel)
        self.tree_frame.grid(row=2, column=0, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # Right Panel (Search, File View) - now in column 1
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # File Listbox and search bar
        self.search_frame = ttk.Frame(self.right_panel)
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.search_frame.grid_columnconfigure(0, weight=1)
        self.search_entry = ttk.Entry(self.search_frame, font=('Arial', 10))
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind('<KeyRelease>', self.search)

        # --- UPDATED TO USE ttk.Treeview FOR SORTABLE COLUMNS ---
        self.file_view = ttk.Treeview(self.right_panel, selectmode=tk.EXTENDED, columns=('size', 'type', 'modified'))
        self.file_view.grid(row=1, column=0, sticky="nsew")
        self.file_view.heading('#0', text='Name', anchor=tk.W, command=lambda: self._sort_by_column('#0'))
        self.file_view.heading('size', text='Size', anchor=tk.E, command=lambda: self._sort_by_column('size'))
        self.file_view.heading('type', text='Type', anchor=tk.W, command=lambda: self._sort_by_column('type'))
        self.file_view.heading('modified', text='Modified', anchor=tk.W, command=lambda: self._sort_by_column('modified'))

        self.file_view.column('#0', width=300, minwidth=150)
        self.file_view.column('size', width=80, minwidth=60, anchor=tk.E)
        self.file_view.column('type', width=80, minwidth=60)
        self.file_view.column('modified', width=150, minwidth=100)

        self.file_view.bind('<Double-1>', self.on_file_double_click)
        
        # --- DRAG AND DROP BINDINGS ---
        self.file_view.bind('<ButtonPress-1>', self.drag_start)
        self.file_view.bind('<B1-Motion>', self.drag_motion)
        self.file_view.bind('<ButtonRelease-1>', self.drag_drop)
        
        # Action buttons frame, now with a two-row layout to prevent buttons from being hidden on small screens
        self.button_frame = ttk.Frame(self, padding="10 0 10 10")
        self.button_frame.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(1, weight=0)

        # Use grid for a two-row layout that is always visible
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)

        # Top row of buttons
        self.up_btn = ttk.Button(self.button_frame, text="Up", command=self.go_up)
        self.up_btn.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.new_folder_btn = ttk.Button(self.button_frame, text="New Folder", command=self.create_folder)
        self.new_folder_btn.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.new_file_btn = ttk.Button(self.button_frame, text="New File", command=self.create_file)
        self.new_file_btn.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
        self.delete_btn = ttk.Button(self.button_frame, text="Delete", command=self.delete_item)
        self.delete_btn.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        
        # Bottom row of buttons
        self.rename_btn = ttk.Button(self.button_frame, text="Rename", command=self.rename_item)
        self.rename_btn.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        self.copy_btn = ttk.Button(self.button_frame, text="Copy", command=self.copy_item)
        self.copy_btn.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.paste_btn = ttk.Button(self.button_frame, text="Paste", command=self.paste_item)
        self.paste_btn.grid(row=1, column=2, padx=5, pady=2, sticky="ew")
        self.undo_btn = ttk.Button(self.button_frame, text="Undo", command=self.undo_last_action)
        self.undo_btn.grid(row=1, column=3, padx=5, pady=2, sticky="ew")

        # Third row for less common actions, centered
        self.button_frame_row3 = ttk.Frame(self, padding="0 0 10 10")
        self.button_frame_row3.grid(row=2, column=0, sticky="ew")
        self.grid_rowconfigure(2, weight=0)

        # Inner frame to hold and center the buttons
        centered_frame = ttk.Frame(self.button_frame_row3)
        centered_frame.pack(expand=True)

        self.refresh_btn = ttk.Button(centered_frame, text="Refresh", command=self.refresh)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=2)
        self.new_window_btn = ttk.Button(centered_frame, text="New Window", command=self.open_new_instance)
        self.new_window_btn.pack(side=tk.LEFT, padx=5, pady=2)

        # Status bar
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, sticky="ew")
        self.grid_rowconfigure(3, weight=0)

        # Populate shortcuts and drives
        self.add_shortcuts()
        self.add_drives()
        
        # Directory Treeview
        self.tree = ttk.Treeview(self.tree_frame, selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_open)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.heading("#0", text="Directory Tree", anchor=tk.W)

        # Populate the tree with lazy loading
        self.populate_tree()
        self.update_file_view()
    
    def open_new_instance(self):
        """Opens a new instance of the file manager."""
        new_app = GUIFileManager()

    def add_shortcuts(self):
        """Adds buttons for common locations to the shortcuts frame."""
        home_path = os.path.expanduser('~')
        downloads_path = os.path.join(home_path, "Downloads")
        docs_path = os.path.join(home_path, "Documents")

        ttk.Button(self.shortcuts_frame, text="Home", command=lambda: self.go_to_path(home_path)).pack(fill=tk.X, pady=2)
        ttk.Button(self.shortcuts_frame, text="Downloads", command=lambda: self.go_to_path(downloads_path)).pack(fill=tk.X, pady=2)
        ttk.Button(self.shortcuts_frame, text="Documents", command=lambda: self.go_to_path(docs_path)).pack(fill=tk.X, pady=2)
        
    def add_drives(self):
        """Adds buttons for system drives to the drives frame."""
        if sys.platform == "win32":
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    ttk.Button(self.drives_frame, text=f"Drive {letter}", command=lambda d=drive: self.go_to_path(d)).pack(fill=tk.X, pady=2)
        else:
            # On Linux/macOS, use the root directory as a shortcut
            ttk.Button(self.drives_frame, text="Root", command=lambda: self.go_to_path("/")).pack(fill=tk.X, pady=2)

    def populate_tree(self, parent_id='', parent_path=None):
        """Populates the directory tree starting from the specified path, with lazy loading."""
        if not parent_path:
            parent_path = os.path.expanduser('~')

        self.tree.delete(*self.tree.get_children())
        self.tree.insert('', 'end', parent_path, text=parent_path, open=True, tags=('folder',))
        self._insert_children(parent_path, parent_path)

    def _insert_children(self, parent_id, parent_path):
        """Helper function to insert child directories for lazy loading."""
        try:
            for item in sorted(os.listdir(parent_path)):
                full_path = os.path.join(parent_path, item)
                if os.path.isdir(full_path):
                    item_id = self.tree.insert(parent_id, 'end', full_path, text=item, tags=('folder',))
                    # Add a dummy item to allow for expansion
                    self.tree.insert(item_id, 'end', text="dummy")
        except PermissionError:
            pass
        except FileNotFoundError:
            pass

    def on_tree_open(self, event):
        """Handles lazy loading when a directory is opened in the tree."""
        item_id = self.tree.focus()
        if not self.tree.get_children(item_id):
            # Check if there's a dummy child and remove it
            if self.tree.get_children(item_id) and self.tree.item(self.tree.get_children(item_id)[0], 'text') == 'dummy':
                self.tree.delete(self.tree.get_children(item_id)[0])
            self._insert_children(item_id, item_id)
            self.tree.focus(item_id)

    def on_tree_select(self, event):
        """Handles directory selection in the Treeview."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        path = selected_item[0]
        self.go_to_path(path)

    def search(self, event):
        """Filters the file list based on search bar input."""
        query = self.search_entry.get().lower()
        self.update_file_view(search_query=query)

    def go_up(self):
        """Moves to the parent directory."""
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path: # Prevent going above the root
            self.go_to_path(parent_path)

    def go_to_path(self, path):
        """Updates the current path and refreshes the display."""
        if os.path.isdir(path):
            self.current_path = path
            self.path_label.config(text=f"Current Path: {self.current_path}")
            self.populate_tree(parent_path=self.current_path)
            self.update_file_view()
        else:
            messagebox.showerror("Error", f"Path not found: {path}")

    def refresh(self):
        """Refreshes the file list and tree view."""
        self.populate_tree(parent_path=self.current_path)
        self.update_file_view()
    
    def _sort_by_column(self, col):
        """Sorts the file view by the clicked column."""
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False  # Start with ascending order for the new column
        
        # Update heading indicators correctly
        for c in ('#0', 'size', 'type', 'modified'):
            text = self.file_view.heading(c)['text'].split(' ')[0]
            self.file_view.heading(c, text=text)
        
        arrow = ' ▼' if self.sort_reverse else ' ▲'
        current_text = self.file_view.heading(col)['text']
        self.file_view.heading(col, text=current_text + arrow)
        
        self.update_file_view()

    def update_file_view(self, search_query=None):
        """Updates the Treeview with file data."""
        items = []
        try:
            for name in os.listdir(self.current_path):
                path = os.path.join(self.current_path, name)
                if search_query and search_query not in name.lower():
                    continue

                try:
                    is_dir = os.path.isdir(path)
                    # For sorting, give folders a size of -1 to group them consistently
                    size = os.path.getsize(path) if not is_dir else -1 
                    mtime = os.path.getmtime(path)
                    file_type = "Folder" if is_dir else self._get_file_type(name)
                    items.append({'name': name, 'path': path, 'is_dir': is_dir, 'size': size, 'mtime': mtime, 'type': file_type})
                except OSError:
                    continue # Skip inaccessible files

            sort_map = {
                '#0': 'name',
                'size': 'size',
                'type': 'type',
                'modified': 'mtime'
            }
            key_to_sort_by = sort_map.get(self.sort_column, 'mtime')
            
            # The key function now correctly groups folders first, then sorts by the selected column
            sort_key_func = lambda x: (not x['is_dir'], x[key_to_sort_by])
            items.sort(key=sort_key_func, reverse=self.sort_reverse)
            
            # Clear old items and insert new ones
            for item in self.file_view.get_children():
                self.file_view.delete(item)

            for item in items:
                display_name = item['name']
                # For display, show folder size as empty, not -1
                size_str = self._format_size(item['size']) if not item['is_dir'] else ''
                mtime_str = datetime.fromtimestamp(item['mtime']).strftime('%Y-%m-%d %H:%M')
                
                self.file_view.insert('', tk.END, text=display_name, values=(size_str, item['type'], mtime_str), tags=(item['path'],))

        except (PermissionError, FileNotFoundError) as e:
            messagebox.showerror("Error", str(e))
        
    def _get_file_type(self, filename):
        """Returns the file type based on its extension."""
        if '.' in filename:
            return filename.split('.')[-1].upper() + " File"
        return "File"
        
    def _format_size(self, size_in_bytes):
        """Formats a size in bytes to a human-readable string (e.g., KB, MB, GB)."""
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024**2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024**3:
            return f"{size_in_bytes / 1024**2:.2f} MB"
        else:
            return f"{size_in_bytes / 1024**3:.2f} GB"

    def _get_selected_item_path(self):
        """Helper to get the full path of the selected item from the Treeview."""
        selected_items = self.file_view.selection()
        if not selected_items:
            return None
        return self.file_view.item(selected_items[0], 'tags')[0]

    def on_file_double_click(self, event):
        """Opens a selected file or directory."""
        selected_path = self._get_selected_item_path()
        if not selected_path:
            return

        if os.path.isdir(selected_path):
            self.go_to_path(selected_path)
        else:
            messagebox.showinfo("File Selected", f"You double-clicked on: {selected_path}")
            # Placeholder for opening file

    # --- HELPER FUNCTION TO GET FOLDER SIZE ---
    def get_folder_size(self, folder_path):
        """Calculates the total size of a folder in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        except (FileNotFoundError, PermissionError):
            return 0
        return total_size

    # --- DRAG AND DROP LOGIC ---
    def drag_start(self, event):
        """Starts the drag operation."""
        try:
            item_id = self.file_view.identify_row(event.y)
            if item_id:
                self.drag_start_item = self.file_view.item(item_id, 'tags')[0]
            else:
                self.drag_start_item = None
        except IndexError:
            self.drag_start_item = None
            
    def drag_motion(self, event):
        """Highlights the destination folder during drag."""
        pass

    def drag_drop(self, event):
        """Completes the drag-and-drop operation (move file)."""
        if not self.drag_start_item:
            return

        drop_item_id = self.file_view.identify_row(event.y)
        if not drop_item_id:
            self.drag_start_item = None
            return

        destination_path = self.file_view.item(drop_item_id, 'tags')[0]
        
        if os.path.isdir(destination_path):
            source_path = self.drag_start_item
            self.move_item(source_path, destination_path)
        
        self.drag_start_item = None

    def move_item(self, source_path, destination_path):
        """Moves an item."""
        # Check for folder size before moving
        if os.path.isdir(source_path):
            size_mb = self.get_folder_size(source_path) / (1024 * 1024)
            if size_mb > 500:
                if not messagebox.askyesno("Large Folder Warning", f"The folder '{os.path.basename(source_path)}' is {size_mb:.2f} MB. Do you want to continue?"):
                    return

        shutil.move(source_path, destination_path)
        self.undo_stack.append({'action': 'move', 'source': source_path, 'destination': destination_path})
        self.refresh()

    # --- FILE MANAGEMENT METHODS ---
    def create_folder(self):
        """Creates a new folder."""
        new_name = filedialog.askstring("New Folder", "Enter new folder name:", parent=self)
        if new_name:
            new_path = os.path.join(self.current_path, new_name)
            os.mkdir(new_path)
            self.undo_stack.append({'action': 'create', 'path': new_path})
            self.refresh()

    def create_file(self):
        """Creates a new file."""
        new_name = filedialog.askstring("New File", "Enter new file name:", parent=self)
        if new_name:
            new_path = os.path.join(self.current_path, new_name)
            with open(new_path, 'w') as f:
                f.write("")
            self.undo_stack.append({'action': 'create', 'path': new_path})
            self.refresh()

    def delete_item(self):
        """Deletes selected file(s) or folder(s)."""
        selected_items = self.file_view.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No item selected to delete.")
            return

        # Check for large folders before proceeding
        for item_id in selected_items:
            full_path = self.file_view.item(item_id, 'tags')[0]
            if os.path.isdir(full_path):
                size_mb = self.get_folder_size(full_path) / (1024 * 1024)
                if size_mb > 500:
                    if not messagebox.askyesno("Large Folder Warning", f"The folder '{os.path.basename(full_path)}' is {size_mb:.2f} MB. Deleting it may take some time. Do you want to continue?"):
                        return # Cancel the entire operation if the user says no

        if not messagebox.askyesno("Delete", "Are you sure you want to delete the selected items?"):
            return
        
        deleted_items = []
        for item_id in selected_items:
            full_path = self.file_view.item(item_id, 'tags')[0]
            
            # Move item to a temporary "recycle bin" for undo
            recycle_path = os.path.join(self.recycle_bin_dir, os.path.basename(full_path))
            if os.path.exists(recycle_path): # Handle name conflicts in recycle bin
                base, ext = os.path.splitext(os.path.basename(recycle_path))
                i = 1
                while os.path.exists(os.path.join(self.recycle_bin_dir, f"{base} ({i}){ext}")):
                    i += 1
                recycle_path = os.path.join(self.recycle_bin_dir, f"{base} ({i}){ext}")
            
            shutil.move(full_path, recycle_path)
            deleted_items.append({'original_path': full_path, 'recycle_path': recycle_path})
        
        if deleted_items:
            self.undo_stack.append({'action': 'delete', 'items': deleted_items})
        
        self.refresh()

    def rename_item(self):
        """Renames a selected file or folder."""
        selection = self.file_view.selection()
        if len(selection) != 1:
            messagebox.showinfo("Info", "Please select exactly one item to rename.")
            return

        item_id = selection[0]
        old_path = self.file_view.item(item_id, 'tags')[0]
        old_name = os.path.basename(old_path)

        new_name = filedialog.askstring("Rename", "Enter new name:", initialvalue=old_name, parent=self)
        if new_name and new_name != old_name:
            new_path = os.path.join(self.current_path, new_name)
            os.rename(old_path, new_path)
            self.undo_stack.append({'action': 'rename', 'old_path': new_path, 'new_path': old_path})
            self.refresh()

    def copy_item(self):
        """Copies selected items to the clipboard."""
        selected_items = self.file_view.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No item selected to copy.")
            return

        # Check for large folders before copying
        for item_id in selected_items:
            full_path = self.file_view.item(item_id, 'tags')[0]
            if os.path.isdir(full_path):
                size_mb = self.get_folder_size(full_path) / (1024 * 1024)
                if size_mb > 500:
                    if not messagebox.askyesno("Large Folder Warning", f"The folder '{os.path.basename(full_path)}' is {size_mb:.2f} MB. Copying it may take some time. Do you want to continue?"):
                        return # Cancel the entire operation if the user says no

        self.clipboard = [self.file_view.item(item_id, 'tags')[0] for item_id in selected_items]
        messagebox.showinfo("Copy", f"{len(self.clipboard)} item(s) copied to clipboard.")
    
    def paste_item(self):
        """Pates items from the clipboard to the current directory."""
        if not self.clipboard:
            messagebox.showinfo("Info", "Clipboard is empty.")
            return

        pasted_paths = []
        for item_path in self.clipboard:
            item_name = os.path.basename(item_path)
            dest_path = os.path.join(self.current_path, item_name)
            
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path)
            else:
                shutil.copy(item_path, dest_path)
            pasted_paths.append(dest_path)
        
        if pasted_paths:
            self.undo_stack.append({'action': 'paste', 'paths': pasted_paths})
        
        self.refresh()

    def undo_last_action(self):
        """Reverses the last recorded action."""
        if not self.undo_stack:
            messagebox.showinfo("Info", "No actions to undo.")
            return
        
        last_action = self.undo_stack.pop()
        action_type = last_action['action']

        if action_type == 'create':
            path_to_delete = last_action['path']
            if os.path.exists(path_to_delete):
                if os.path.isdir(path_to_delete):
                    shutil.rmtree(path_to_delete)
                else:
                    os.remove(path_to_delete)
            messagebox.showinfo("Undo", "Undid file/folder creation.")

        elif action_type == 'delete':
            for item in last_action['items']:
                original_path = item['original_path']
                recycle_path = item['recycle_path']
                shutil.move(recycle_path, original_path)
            messagebox.showinfo("Undo", "Undid deletion.")

        elif action_type == 'rename':
            old_path = last_action['old_path']
            new_path = last_action['new_path']
            os.rename(old_path, new_path)
            messagebox.showinfo("Undo", "Undid renaming.")

        elif action_type == 'move':
            source = last_action['source']
            destination = last_action['destination']
            shutil.move(destination, source)
            messagebox.showinfo("Undo", "Undid move.")

        elif action_type == 'paste':
            for path_to_delete in last_action['paths']:
                if os.path.exists(path_to_delete):
                    if os.path.isdir(path_to_delete):
                        shutil.rmtree(path_to_delete)
                    else:
                        os.remove(path_to_delete)
            messagebox.showinfo("Undo", "Undid pasting.")
        
        self.refresh()

if __name__ == "__main__":
    app = GUIFileManager()
    app.mainloop()
