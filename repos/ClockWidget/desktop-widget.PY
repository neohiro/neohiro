import tkinter as tk
from tkinter import ttk, colorchooser
from datetime import datetime
import pytz
import json
import os
import sys
import threading
import platform
import ctypes # Required for the Win+D fix

# --- NEW: Import winreg for Windows Startup ---
try:
    if platform.system() == "Windows":
        import winreg
except ImportError:
    winreg = None
# --- END NEW ---

# Optional tray support
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None


# --- Startup Management (OS-Specific) ---
APP_NAME = "DesktopClockWidget"
EXECUTABLE_PATH = sys.executable
SCRIPT_PATH = os.path.abspath(__file__)
STARTUP_COMMAND = f'"{EXECUTABLE_PATH}" "{SCRIPT_PATH}"'


def enable_startup():
    """Adds the script to the system's startup list."""
    if platform.system() == "Windows":
        if not winreg:
            print("winreg module not found. Cannot enable Windows startup.")
            return False
        try:
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as startup_key:
                winreg.SetValueEx(startup_key, APP_NAME, 0, winreg.REG_SZ, STARTUP_COMMAND)
            print(f"Windows startup enabled via Registry: {key_path}\\{APP_NAME}")
            return True
        except Exception as e:
            print(f"Error enabling Windows startup via Registry: {e}")
            return False
            
    elif platform.system() == "Linux":
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            desktop_file_path = os.path.join(autostart_dir, f"{APP_NAME}.desktop")
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={STARTUP_COMMAND}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
            with open(desktop_file_path, "w") as f:
                f.write(desktop_content)
            print(f"Linux startup enabled via: {desktop_file_path}")
            return True
        except Exception as e:
            print(f"Error enabling Linux startup: {e}")
            return False
            
    elif platform.system() == "Darwin": 
        print("macOS startup management is complex (Launch Agents) and not implemented in this minimal example.")
        return False
        
    else:
        print(f"Startup management for {platform.system()} is not implemented.")
        return False


def disable_startup():
    """Removes the script from the system's startup list."""
    if platform.system() == "Windows":
        if not winreg:
            return False
        try:
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as startup_key:
                try:
                    winreg.DeleteValue(startup_key, APP_NAME)
                    print(f"Windows startup disabled: Registry key {key_path}\\{APP_NAME} removed.")
                    return True
                except FileNotFoundError:
                    # If key is not found, it's already disabled. Return True to allow UI to update.
                    return True
        except Exception as e:
            print(f"Error disabling Windows startup via Registry: {e}")
            return False
            
    elif platform.system() == "Linux":
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file_path = os.path.join(autostart_dir, f"{APP_NAME}.desktop")
            if os.path.exists(desktop_file_path):
                os.remove(desktop_file_path)
                print(f"Linux startup disabled: {desktop_file_path} removed.")
                return True
            return True # Return True if file didn't exist (already disabled)
        except Exception as e:
            print(f"Error disabling Linux startup: {e}")
            return False
            
    elif platform.system() == "Darwin":
        return False
        
    else:
        return False


# --- Settings persistence ---
SETTINGS_FILE = os.path.expanduser("~/.desktop_clock_settings.json")


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {}


DEFAULT_FONT = "Segoe UI"
DEFAULT_TIME_SIZE = 48
DEFAULT_DATE_SIZE = 16
UPDATE_INTERVAL = 1000

# Key for transparency. Any pixel this color is "invisible" and click-through.
BACKGROUND_COLOR = "#000001" 
# UPDATED: Set to same as background so it is visually transparent.
CLICKABLE_BG = BACKGROUND_COLOR


# --- Clock Widget ---
class DesktopClock:
    def __init__(self, manager, root, name="Local", tz=None, small=False):
        self.manager = manager
        self.root = root
        self.name = name
        self.tz = tz
        self.small = small
        self._is_dragging = False 

        all_settings = load_settings()
        self.settings = all_settings.get(self.name, {})

        default_color = "white"
        if "Local" in all_settings:
            default_color = all_settings["Local"].get("text_color", default_color)

        self.text_color = tk.StringVar(value=self.settings.get("text_color", default_color))
        self.hour_format = tk.StringVar(value=self.settings.get("hour_format", "24h"))
        self.widget_size = tk.StringVar(value=self.settings.get("widget_size", "Medium"))
        self.show_date = tk.BooleanVar(value=self.settings.get("show_date", True))
        # --- MODIFICATION: New setting for showing seconds ---
        self.show_seconds = tk.BooleanVar(value=self.settings.get("show_seconds", True)) 
        # --- END MODIFICATION ---
        self.topmost = self.settings.get("topmost", True)
        
        if self.name == "Local":
            self.startup = self.settings.get("startup", False) 
            self.world_clock_side = tk.StringVar(value=self.settings.get("world_clock_side", "Right"))
        else:
            self.startup = False
            self.world_clock_side = tk.StringVar(value="Right")


        self.root.overrideredirect(True)

        # --- FIX FOR WIN+D ---
        # This block modifies the window style to be a "Tool Window" (WS_EX_TOOLWINDOW).
        # Windows treats tool windows differently: they don't minimize when you press Win+D.
        if platform.system() == "Windows":
            self.root.update_idletasks() # Ensure window handle exists
            try:
                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080
                
                # Get the actual window handle (HWND)
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0:
                    hwnd = self.root.winfo_id()
                
                # Get current styles
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                
                # Modify styles: Remove AppWindow, Add ToolWindow
                style = style & ~WS_EX_APPWINDOW
                style = style | WS_EX_TOOLWINDOW
                
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                
                # Refresh the window to apply style changes
                self.root.wm_withdraw()
                self.root.wm_deiconify()
            except Exception as e:
                print(f"Could not set ToolWindow style (Win+D fix): {e}")
        # --- END FIX ---

        self.root.config(bg=BACKGROUND_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", BACKGROUND_COLOR)
        except:
            pass
        self.root.wm_attributes("-topmost", self.topmost)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray if not small else self.root.destroy)

        self.main_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Timezone label
        self.tz_label = tk.Label(
            self.main_frame,
            font=(DEFAULT_FONT, DEFAULT_DATE_SIZE - 2),
            fg=self.text_color.get(),
            bg=BACKGROUND_COLOR
        )
        if self.name != "Local":
            self.tz_label.grid(row=0, column=0, pady=(5,0), padx=(10,5), sticky="e") 

        # Time & Date labels
        self.time_label = tk.Label(
            self.main_frame,
            font=(DEFAULT_FONT, DEFAULT_TIME_SIZE, "bold"),
            fg=self.text_color.get(),
            bg=BACKGROUND_COLOR
        )
        time_row = 1 if self.name != "Local" else 0 
        self.time_label.grid(row=time_row, column=0, pady=(5,0), padx=(10,5), sticky="e")

        self.date_label = tk.Label(
            self.main_frame,
            font=(DEFAULT_FONT, DEFAULT_DATE_SIZE),
            fg=self.text_color.get(),
            bg=BACKGROUND_COLOR
        )
        date_row = 2 if self.name != "Local" else 1
        self.date_label.grid(row=date_row, column=0, pady=(0,5), padx=(10,5), sticky="e")

        # Settings button
        if not small:
            # UPDATED: Use transparent background, but keep structure for spacing
            self.settings_frame = tk.Frame(self.main_frame, bg=CLICKABLE_BG) 
            self.settings_frame.grid(row=time_row, column=1, rowspan=2, pady=(10,10), padx=(5,10), sticky="n")
            
            self.settings_button = tk.Label(
                self.settings_frame,
                text="⚙️",
                font=(DEFAULT_FONT, 18),
                bg=CLICKABLE_BG, 
                fg=self.text_color.get(),
                cursor="hand2"
            )
            # Keep padding to push other elements away, even if the space is transparent
            self.settings_button.pack(padx=2, pady=2, ipadx=4, ipady=4) 
            
            # Bindings
            drag_widgets = [self.time_label, self.date_label, self.main_frame, self.tz_label] 
            
            for w in drag_widgets:
                w.bind("<Button-1>", self.start_move)
                w.bind("<B1-Motion>", self.do_move)

            # Bind Drag/Click to button and frame
            self.settings_button.bind("<Button-1>", self.start_move) 
            self.settings_button.bind("<B1-Motion>", self.do_move) 
            self.settings_button.bind("<ButtonRelease-1>", self.open_settings_on_release)
            
            self.settings_frame.bind("<Button-1>", self.start_move) 
            self.settings_frame.bind("<B1-Motion>", self.do_move) 
            self.settings_frame.bind("<ButtonRelease-1>", self.open_settings_on_release) 

        self.drag_x_root = 0 
        self.drag_y_root = 0

        self.apply_settings()
        self.update_clock()

    
    # --- DRAG/CLICK METHODS ---
    def update_clock(self):
        try:
            now = datetime.now(pytz.timezone(self.tz)) if self.tz else datetime.now()
        except pytz.exceptions.UnknownTimeZoneError:
            now = datetime.now()

        # --- MODIFICATION: Apply show_seconds setting to time format ---
        time_format_base = "%H:%M" if self.hour_format.get() == "24h" else "%I:%M %p"
        seconds_suffix = ":%S" if self.show_seconds.get() else ""
        
        # Insert seconds before %p for 12h format if needed
        if self.hour_format.get() == "12h" and seconds_suffix:
            fmt = time_format_base.replace(" %p", seconds_suffix + " %p")
        else:
            fmt = time_format_base + seconds_suffix
            
        self.time_label.config(text=now.strftime(fmt))
        # --- END MODIFICATION ---
        
        self.date_label.config(text=now.strftime("%A, %b %d, %Y"))
        
        if self.tz:
            self.tz_label.config(text=self.tz.split('/')[-1].replace('_', ' '))
        
        self.root.after(UPDATE_INTERVAL, self.update_clock)

    def start_move(self, event):
        self.drag_x_root = event.x_root 
        self.drag_y_root = event.y_root
        self._is_dragging = False 

    def do_move(self, event):
        if abs(event.x_root - self.drag_x_root) > 2 or abs(event.y_root - self.drag_y_root) > 2:
             self._is_dragging = True 

        dx = event.x_root - self.drag_x_root
        dy = event.y_root - self.drag_y_root
        
        self.manager.move_cluster(dx, dy)
        
        self.drag_x_root = event.x_root
        self.drag_y_root = event.y_root

    def open_settings_on_release(self, event):
        if not self._is_dragging:
            # Allow event to trigger if it came from button OR the frame container
            if event.widget in [self.settings_button, self.settings_frame]:
                self.open_settings(event)
        
    def apply_settings(self, *args): # Added *args to allow binding to trace
        size = self.widget_size.get()
        if size == "Small":
            time_size, date_size = 32, 12
        elif size == "Medium":
            time_size, date_size = 48, 16
        else: # Large
            time_size, date_size = 72, 24
        
        if self.small:
            time_size //= 2
            date_size //= 2

        self.time_label.config(font=(DEFAULT_FONT, time_size, "bold"))
        self.date_label.config(font=(DEFAULT_FONT, date_size))
        self.tz_label.config(font=(DEFAULT_FONT, date_size - 2)) 

        color = self.text_color.get()
        self.time_label.config(fg=color)
        self.date_label.config(fg=color)
        self.tz_label.config(fg=color)
        
        if not self.small:
            self.settings_button.config(fg=color)

        if self.show_date.get():
            self.date_label.grid()
        else:
            self.date_label.grid_remove()

        self.root.wm_attributes("-topmost", self.topmost)
        self.update_clock() # Trigger update to apply new seconds format
        
        if not self.small:
            # UPDATED: Increased gear size slightly (from /4 to /3) to make the target larger
            # since the background is now transparent/click-through.
            gear_size = max(10, time_size // 3) 
            self.settings_button.config(font=(DEFAULT_FONT, gear_size))

        self.save_settings()

    def save_settings(self):
        all_settings = load_settings()
        
        clock_settings = {
            "hour_format": self.hour_format.get(),
            "widget_size": self.widget_size.get(),
            "text_color": self.text_color.get(),
            "show_date": self.show_date.get(),
            "show_seconds": self.show_seconds.get(), # --- MODIFICATION: Save show_seconds ---
            "topmost": self.topmost,
        }
        
        if self.name == "Local":
            clock_settings["world_clocks"] = self.manager.world_clocks
            clock_settings["startup"] = self.startup
            clock_settings["world_clock_side"] = self.world_clock_side.get()
            
            if self.root.winfo_exists():
                geom = self.root.geometry().split('+')
                if len(geom) == 3: 
                    clock_settings["x"] = int(geom[1])
                    clock_settings["y"] = int(geom[2])

        all_settings[self.name] = clock_settings
        save_settings(all_settings)

    # --- Settings Window ---
    def open_settings(self, event=None):
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            return


        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title(f"{self.name} Settings")
        self.settings_window.resizable(False, False)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.settings_window.withdraw)
        
        # New: Use a main frame for padding and structure
        main_settings_frame = ttk.Frame(self.settings_window, padding="10")
        main_settings_frame.grid(row=0, column=0, sticky="nsew")
        self.settings_window.grid_columnconfigure(0, weight=1)

        row = 0

        # Bindings for instantaneous updates
        self.hour_format.trace_add("write", self.apply_settings)
        self.widget_size.trace_add("write", self.apply_settings)
        self.show_date.trace_add("write", self.apply_settings)
        self.show_seconds.trace_add("write", self.apply_settings)
        
        if self.name == "Local":
            self.world_clock_side.trace_add("write", lambda *args: (self.manager.set_world_clock_side(self.world_clock_side.get()), self.apply_settings()))
        
        # --- General Settings ---
        # Hour format
        tk.Label(main_settings_frame, text="Hour Format:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        hour_combo = ttk.Combobox(main_settings_frame, textvariable=self.hour_format, values=["12h", "24h"], state="readonly")
        hour_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Widget size
        tk.Label(main_settings_frame, text="Widget Size:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        size_combo = ttk.Combobox(main_settings_frame, textvariable=self.widget_size, values=["Small", "Medium", "Large"], state="readonly")
        size_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Text color
        tk.Label(main_settings_frame, text="Text Color:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        color_btn = tk.Button(main_settings_frame, text="Choose Color", command=self.choose_color)
        color_btn.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Checkboxes in one row for better alignment
        checkbox_frame = ttk.Frame(main_settings_frame)
        checkbox_frame.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        checkbox_frame.grid_columnconfigure(0, weight=1)
        checkbox_frame.grid_columnconfigure(1, weight=1)

        # Show date
        show_date_chk = tk.Checkbutton(checkbox_frame, text="Show Date", variable=self.show_date)
        show_date_chk.grid(row=0, column=0, sticky="w")
        
        # --- MODIFICATION: New setting for showing seconds ---
        show_seconds_chk = tk.Checkbutton(checkbox_frame, text="Show Seconds", variable=self.show_seconds)
        show_seconds_chk.grid(row=0, column=1, sticky="e")
        # --- END MODIFICATION ---
        
        row += 1
        
        # Topmost
        self.topmost_var = tk.BooleanVar(value=self.topmost)
        # BINDING CHANGE: Call toggle directly
        topmost_chk = tk.Checkbutton(main_settings_frame, text="Always on Top", variable=self.topmost_var, command=self.toggle_topmost)
        topmost_chk.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        
        if self.name == "Local":
            # --- Local Clock Specific Settings ---
            
            ttk.Separator(main_settings_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 5))
            row += 1

            self.startup_var = tk.BooleanVar(value=self.startup)
            # BINDING CHANGE: Call toggle directly
            startup_chk = tk.Checkbutton(main_settings_frame, text="Start on System Startup", variable=self.startup_var, command=self.toggle_startup)
            startup_chk.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
            row += 1
            
            tk.Label(main_settings_frame, text="World Clock Side:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            side_combo = ttk.Combobox(main_settings_frame, textvariable=self.world_clock_side, values=["Right", "Left"], state="readonly")
            side_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            row += 1
            
            # --- Add World Clock ---
            ttk.Separator(main_settings_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 5))
            row += 1
            tk.Label(main_settings_frame, text="--- Add World Clock ---").grid(row=row, column=0, columnspan=2, pady=(0, 5))
            row += 1

            tk.Label(main_settings_frame, text="Timezone:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            self.world_tz_var = tk.StringVar()
            tz_list = sorted(pytz.all_timezones)
            tz_combo = ttk.Combobox(main_settings_frame, textvariable=self.world_tz_var, values=tz_list, state="readonly")
            tz_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            row += 1

            add_btn = tk.Button(main_settings_frame, text="Add Clock", command=self.add_world_clock)
            add_btn.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
            row += 1
            
            # --- Active World Clocks ---
            ttk.Separator(main_settings_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 5))
            row += 1
            tk.Label(main_settings_frame, text="--- Active World Clocks ---").grid(row=row, column=0, columnspan=2, pady=(0, 5))
            row += 1

            listbox_frame = tk.Frame(main_settings_frame)
            listbox_frame.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
            
            listbox_height = max(3, len(self.manager.world_clocks))
            
            self.active_clocks_listbox = tk.Listbox(listbox_frame, height=listbox_height, selectmode=tk.SINGLE)
            self.active_clocks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.active_clocks_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.active_clocks_listbox.config(yscrollcommand=scrollbar.set)
            
            self._populate_active_clocks_listbox()
            
            row += 1

            remove_btn = tk.Button(main_settings_frame, text="Remove Selected Clock", command=self.remove_selected_world_clock)
            remove_btn.grid(row=row, column=0, columnspan=2, pady=5, sticky="ew")
            row += 1

        
        # REMOVED: Apply button

        # Quit button
        quit_btn = tk.Button(main_settings_frame, text="Quit Application", command=self.exit_app, fg="red")
        quit_btn.grid(row=row, column=0, columnspan=2, pady=(20, 5), sticky="ew")
        
        # Configure columns to expand
        main_settings_frame.grid_columnconfigure(1, weight=1)

        
    def _populate_active_clocks_listbox(self):
        self.active_clocks_listbox.delete(0, tk.END)
        for tz in self.manager.world_clocks:
            self.active_clocks_listbox.insert(tk.END, tz)

    def choose_color(self):
        color = colorchooser.askcolor(title="Select Text Color", color=self.text_color.get(), parent=self.settings_window)
        if color[1]:
            new_color = color[1]
            self.text_color.set(new_color)
            self.apply_settings() 
            if self.name == "Local":
                self.manager.update_all_clock_colors(new_color)

    def toggle_topmost(self):
        self.topmost = self.topmost_var.get()
        self.root.wm_attributes("-topmost", self.topmost)
        self.save_settings()
        
    def toggle_startup(self):
        new_state = self.startup_var.get()
        success = enable_startup() if new_state else disable_startup()
        
        if success:
            self.startup = new_state
        else:
            self.startup = not new_state
            self.startup_var.set(not new_state) 
        
        if self.name == "Local":
            self.manager.startup = self.startup
            self.save_settings()

    # REMOVED: apply_all_settings - logic moved to individual setting functions

    def add_world_clock(self):
        tz = self.world_tz_var.get()
        if tz and tz not in self.manager.world_clocks: 
            self.manager.world_clocks.append(tz) 
            
            current_color = self.text_color.get()
            self.manager.create_world_clock(tz, initial_color=current_color)
            
            self.manager.arrange_world_clocks()
            self._populate_active_clocks_listbox() 
            self.save_settings()
            self.world_tz_var.set('') 

    def remove_selected_world_clock(self):
        selected_indices = self.active_clocks_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            tz_to_remove = self.active_clocks_listbox.get(index)
            self.manager.remove_world_clock(tz_to_remove)
            self._populate_active_clocks_listbox() 
            new_height = max(3, len(self.manager.world_clocks))
            self.active_clocks_listbox.config(height=new_height)
            self.save_settings()
            
    # --- System Tray ---
    def minimize_to_tray(self):
        self.root.withdraw()
        if pystray:
            def create_icon():
                img = Image.new("RGB", (64, 64), color="black")
                d = ImageDraw.Draw(img)
                d.text((10, 20), "⏰", fill="white", font=Image.core.getfont(None, 40)) 
                
                if not hasattr(self.manager, 'tray_icon') or self.manager.tray_icon is None:
                    self.manager.tray_icon = pystray.Icon("DesktopClock", img, "Desktop Clock", menu=pystray.Menu(
                        pystray.MenuItem("Open", self.restore_from_tray, default=True),
                        pystray.MenuItem("Exit", self.exit_app)
                    ))
                    self.manager.tray_icon.run()
                else:
                    pass

            if not hasattr(self.manager, 'tray_icon') or self.manager.tray_icon is None:
                threading.Thread(target=create_icon, daemon=True).start()


    def restore_from_tray(self):
        if hasattr(self.manager, 'tray_icon') and self.manager.tray_icon is not None:
            try:
                self.manager.tray_icon.stop()
                self.manager.tray_icon = None 
            except:
                pass
        
        self.root.deiconify()
        for win, _ in self.manager.world_clock_windows.values():
            win.deiconify()

    def exit_app(self):
        if hasattr(self.manager, 'tray_icon') and self.manager.tray_icon is not None:
            try:
                self.manager.tray_icon.stop() 
            except:
                pass
        self.root.destroy()
        sys.exit(0)


# --- Clock Manager ---
class ClockManager:
    def __init__(self, master):
        self.master = master
        self.clocks = []
        self.world_clocks = []
        self.world_clock_windows = {}
        self.startup = False
        self.world_clock_side = "Right" 
        self.local_clock_window = None
        self.tray_icon = None 

    def set_world_clock_side(self, side):
        """Sets the side and immediately rearranges clocks."""
        self.world_clock_side = side
        self.arrange_world_clocks()

    def create_world_clock(self, tz, initial_color=None):
        if tz not in self.world_clock_windows:
            win = tk.Toplevel(self.master)
            clock = DesktopClock(self, win, name=tz, tz=tz, small=True)
            
            if initial_color:
                clock.text_color.set(initial_color)
                clock.apply_settings() 
            
            self.world_clock_windows[tz] = (win, clock)
            self.clocks.append(clock)
            return clock 

    def remove_world_clock(self, tz):
        if tz in self.world_clock_windows:
            win, clock = self.world_clock_windows.pop(tz)
            win.destroy()
            if clock in self.clocks:
                self.clocks.remove(clock)
            if tz in self.world_clocks:
                self.world_clocks.remove(tz)
            self.arrange_world_clocks()
            
    def update_all_clock_colors(self, new_color):
        for tz in self.world_clocks:
            if tz in self.world_clock_windows:
                _, clock_instance = self.world_clock_windows[tz]
                clock_instance.text_color.set(new_color)
                clock_instance.apply_settings()

    def arrange_world_clocks(self):
        if not self.local_clock_window:
            return
        self.local_clock_window.update_idletasks() 
        
        lx = self.local_clock_window.winfo_x()
        ly = self.local_clock_window.winfo_y()
        l_width = self.local_clock_window.winfo_width()
        
        offset_y = ly 
        spacing = 10 
        
        sorted_world_clocks = sorted(self.world_clocks) 
        
        if self.world_clock_side == "Right":
            x_start = lx + l_width
        else: 
            # Get the width of the first world clock to calculate starting x for 'Left' side
            # We need to sum up the width and spacing of all clocks to place them correctly.
            total_world_width = sum(
                self.world_clock_windows[tz][0].winfo_width() + spacing
                for tz in sorted_world_clocks if tz in self.world_clock_windows
            )
            # Adjust total width calculation to exclude the last spacing added by the loop below
            total_world_width = max(0, total_world_width - spacing)
            
            x_start = lx - total_world_width - spacing
            
        current_x = x_start 

        for tz in sorted_world_clocks:
            if tz in self.world_clock_windows:
                win, clock = self.world_clock_windows[tz]
                win.update_idletasks()
                w_width = win.winfo_width()
                
                # REVISED: 'Left' side placement logic
                if self.world_clock_side == "Left":
                    # Place at current_x, then advance for the next one
                    new_x = current_x 
                    # The next clock starts after the current one's width and spacing
                    current_x += w_width + spacing
                else: 
                    # Place at current_x, then advance for the next one
                    new_x = current_x
                    current_x += w_width + spacing
                    
                win.geometry(f"+{new_x}+{offset_y}")
                
                offset_y += win.winfo_height() + spacing


    def move_cluster(self, dx, dy):
        if self.local_clock_window:
            lx = self.local_clock_window.winfo_x()
            ly = self.local_clock_window.winfo_y()
            self.local_clock_window.geometry(f"+{lx + dx}+{ly + dy}")
            
            for win, _ in self.world_clock_windows.values():
                wx = win.winfo_x()
                wy = win.winfo_y()
                win.geometry(f"+{wx + dx}+{wy + dy}")
            
            if self.clocks:
                self.clocks[0].save_settings()


    def run(self):
        settings = load_settings()

        # 1. Create Local Clock
        local_root = self.master
        local_clock = DesktopClock(self, local_root, name="Local")
        self.clocks.append(local_clock)
        self.local_clock_window = local_root 
        self.startup = local_clock.startup 
        self.world_clock_side = local_clock.world_clock_side.get()

        if "Local" in settings and "x" in settings["Local"] and "y" in settings["Local"]:
            x = settings["Local"]["x"]
            y = settings["Local"]["y"]
            local_root.geometry(f"+{x}+{y}")
        else:
            local_root.update_idletasks()
            screen_width = local_root.winfo_screenwidth()
            clock_width = local_root.winfo_width()
            local_root.geometry(f"+{screen_width - clock_width - 20}+{20}")


        # 2. Create World Clocks
        self.world_clocks = settings.get("Local", {}).get("world_clocks", [])
        
        initial_color = local_clock.text_color.get()
        
        for tz in self.world_clocks:
            self.create_world_clock(tz, initial_color=initial_color)

        # 3. Arrange world clocks
        self.arrange_world_clocks()
        
        # 4. Start main loop
        self.master.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    manager = ClockManager(root)
    manager.run()
