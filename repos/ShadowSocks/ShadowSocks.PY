import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import sys
import os
import json
import appdirs
import atexit
from queue import Queue, Empty
import time
import re

# Conditional imports for Windows Registry and tray icon libraries
if os.name == 'nt':
    import winreg

try:
    from pystray import MenuItem as Item, Icon
    from PIL import Image, ImageDraw
except ImportError:
    pass

# --- Constants & Global Paths ---
APP_NAME = "ShadowsocksClient"
APP_AUTHOR = "FrenzyPenguin Media"
DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LOCK_FILE = os.path.join(DATA_DIR, "shadowsocks_client.lock")

# --- Utility Functions ---

def acquire_lock():
    """Acquires a lock file to ensure only one instance of the application is running."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read())
            # Check if the process is still running
            if os.name == 'nt':
                import ctypes
                if ctypes.windll.kernel32.GetProcessId(
                        ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)) != 0:
                    return False
            else:
                if os.path.exists(f'/proc/{pid}'):
                    return False
        except (IOError, ValueError):
            pass
        
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass

    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except (IOError, PermissionError) as e:
        messagebox.showerror("Error", f"Could not create lock file: {e}")
        return False

def release_lock():
    """Releases the lock file on program exit."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError as e:
        print(f"Failed to remove lock file: {e}")

def is_startup_enabled():
    """Checks if the application is set to start with the system."""
    if sys.platform.startswith('linux'):
        autostart_dir = os.path.join(os.path.expanduser('~'), '.config', 'autostart')
        desktop_file_path = os.path.join(autostart_dir, 'shadowsocks.desktop')
        return os.path.exists(desktop_file_path)
    elif os.name == 'nt':
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except (FileNotFoundError, WindowsError):
            return False
    return False

# --- Main Application Class ---

class ShadowsocksClientApp:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._setup_dark_theme()

        self.ss_process = None
        self.config = {}
        self.ui_queue = Queue()
        self.latency_running = False
        self.latency_thread = None
        
        self.load_config()
        self._setup_ui()
        
        atexit.register(self.disconnect_proxy)
        self.root.after(100, self._process_ui_queue)

        self.tray_icon = None
        threading.Thread(target=self._setup_tray_icon, daemon=True).start()

    def _setup_window(self):
        """Configures the main window properties."""
        self.root.title("Shadowsocks Client")
        self.root.geometry("400x420")
        self.root.resizable(False, True)
        self.root.configure(bg="#1E1E1E")
        self.set_window_icon("icon.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

    def _setup_dark_theme(self):
        """Applies a custom dark theme to Tkinter widgets."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        
        DARK_BACKGROUND = "#1E1E1E"
        DARK_FOREGROUND = "#A0A0A0"
        PRIMARY_COLOR = "#00C0FF"
        ENTRY_BACKGROUND = "#2A2A2A"
        ENTRY_FOREGROUND = "#E0E0E0"
        
        style.configure("TFrame", background=DARK_BACKGROUND)
        style.configure("TLabel", background=DARK_BACKGROUND, foreground=DARK_FOREGROUND, font=("Consolas", 10))
        style.configure("TEntry", fieldbackground=ENTRY_BACKGROUND, foreground=ENTRY_FOREGROUND, borderwidth=1, relief="flat", font=("Consolas", 10))
        style.map("TEntry", fieldbackground=[("focus", PRIMARY_COLOR)])
        style.configure("TCombobox", fieldbackground=ENTRY_BACKGROUND, foreground=ENTRY_FOREGROUND, selectbackground=PRIMARY_COLOR, selectforeground=ENTRY_FOREGROUND, borderwidth=1, relief="flat", font=("Consolas", 10))
        style.map("TCombobox", fieldbackground=[("readonly", ENTRY_BACKGROUND)])
        style.configure("TButton", background=PRIMARY_COLOR, foreground=DARK_BACKGROUND, font=("Consolas", 10, "bold"), borderwidth=0, relief="flat")
        style.map("TButton", background=[("active", "#3A3A3A")], foreground=[("active", PRIMARY_COLOR)])
        style.configure("TCheckbutton", background=DARK_BACKGROUND, foreground=DARK_FOREGROUND, font=("Consolas", 10))
        style.map("TCheckbutton", background=[("active", DARK_BACKGROUND)], foreground=[("active", PRIMARY_COLOR)])

    def _setup_ui(self):
        """Creates and packs all UI elements."""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Shadowsocks Client", font=("Consolas", 16, "bold"), foreground="#00C0FF").pack(pady=(0, 10))

        # Input fields
        self._create_input_field(main_frame, "Server Address:", "entry_server")
        self._create_input_field(main_frame, "Server Port:", "entry_port")
        self._create_password_field(main_frame, "Password:")
        self._create_encryption_combobox(main_frame)
        self._create_input_field(main_frame, "Local Port:", "entry_local_port")

        # Status and latency
        status_and_latency_frame = ttk.Frame(main_frame)
        status_and_latency_frame.pack(fill="x", pady=(10, 5))
        self.status_label = ttk.Label(status_and_latency_frame, text="Status: Disconnected", foreground="#FF5733", font=("Consolas", 12))
        self.status_label.pack(side="left", expand=True, fill="x")
        self.latency_label = ttk.Label(status_and_latency_frame, text="Latency: N/A", foreground="#A0A0A0", font=("Consolas", 12))
        self.latency_label.pack(side="right", expand=True, fill="x")
        
        self.info_label = ttk.Label(main_frame, text="", wraplength=350, justify="center", font=("Consolas", 10, "italic"), foreground="#A0A0A0")
        self.info_label.pack(pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(button_frame, text="Connect", command=self.connect_proxy).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(button_frame, text="Disconnect", command=self.disconnect_proxy).pack(side="right", expand=True, fill="x", padx=(5, 0))

        # Startup checkbox
        self.startup_var = tk.BooleanVar()
        startup_check = ttk.Checkbutton(main_frame, text="Start with system", variable=self.startup_var, command=self.toggle_startup_setting)
        startup_check.pack(pady=(10, 0))
        
        self.apply_config_to_ui()
        self.startup_var.set(is_startup_enabled())

    def _create_input_field(self, parent, label_text, entry_name, show=None):
        """Helper to create a labelled input field."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text=label_text, width=20).pack(side="left", padx=(0, 10))
        entry = ttk.Entry(frame, show=show)
        entry.pack(side="right", expand=True, fill="x")
        setattr(self, entry_name, entry)
    
    def _create_password_field(self, parent, label_text):
        """Helper to create a password field with a show/hide button."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text=label_text, width=20).pack(side="left", padx=(0, 10))
        
        inner_frame = ttk.Frame(frame)
        inner_frame.pack(side="right", expand=True, fill="x")
        
        self.entry_password = ttk.Entry(inner_frame, show="*")
        self.entry_password.pack(side="left", expand=True, fill="x")
        
        self.show_password_btn = ttk.Button(inner_frame, text="Show", command=self._toggle_password_visibility)
        self.show_password_btn.pack(side="right", padx=(5, 0))

    def _toggle_password_visibility(self):
        """Toggles the visibility of the password field."""
        if self.entry_password.cget("show") == "*":
            self.entry_password.config(show="")
            self.show_password_btn.config(text="Hide")
        else:
            self.entry_password.config(show="*")
            self.show_password_btn.config(text="Show")

    def _create_encryption_combobox(self, parent):
        """Helper to create the encryption method dropdown with a comprehensive list."""
        methods = [
            # AEAD Ciphers (Recommended)
            "2022-blake3-aes-128-gcm",
            "2022-blake3-aes-256-gcm",
            "2022-blake3-chacha20-poly1305",
            "aes-256-gcm", 
            "aes-128-gcm", 
            "chacha20-ietf-poly1305", 
            "xchacha20-ietf-poly1305",

            # Other Ciphers (Less secure, but for compatibility)
            "aes-256-cfb",
            "aes-128-cfb",
            "chacha20",
            "chacha20-ietf",
            "bf-cfb",
            "rc4-md5",
            "none"
        ]
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text="Encryption Method:", width=20).pack(side="left", padx=(0, 10))
        self.entry_method = ttk.Combobox(frame, state="readonly", values=methods)
        self.entry_method.set("aes-256-gcm")
        self.entry_method.pack(side="right", expand=True, fill="x")

    def set_window_icon(self, icon_path):
        """Sets the application window icon."""
        try:
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            print(f"Warning: Failed to set window icon. File '{icon_path}' not found.")

    def load_config(self):
        """Loads configuration from file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
                    self.root.geometry(self.config.get("window_geometry", "400x420"))
            except (IOError, json.JSONDecodeError):
                print("Failed to load config file. Using defaults.")
        self.config.setdefault("server", "127.0.0.1")
        self.config.setdefault("port", "8388")
        self.config.setdefault("password", "")
        self.config.setdefault("method", "aes-256-gcm")
        self.config.setdefault("local_port", "1080")
        self.config.setdefault("startup_enabled", False)

    def save_config(self):
        """Saves current UI state to configuration file."""
        self.config.update({
            "server": self.entry_server.get(),
            "port": self.entry_port.get(),
            "password": self.entry_password.get(),
            "method": self.entry_method.get(),
            "local_port": self.entry_local_port.get(),
            "startup_enabled": self.startup_var.get(),
            "window_geometry": self.root.geometry()
        })
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except (IOError, PermissionError) as e:
            print(f"Failed to save configuration file: {e}")

    def apply_config_to_ui(self):
        """Populates UI with loaded configuration."""
        self.entry_server.insert(0, self.config["server"])
        self.entry_port.insert(0, self.config["port"])
        self.entry_password.insert(0, self.config["password"])
        self.entry_method.set(self.config["method"])
        self.entry_local_port.insert(0, self.config["local_port"])

    def _process_ui_queue(self):
        """Processes UI updates from a queue to prevent blocking."""
        try:
            while True:
                task = self.ui_queue.get_nowait()
                task()
                self.ui_queue.task_done()
        except Empty:
            pass
        self.root.after(100, self._process_ui_queue)

    def _queue_ui_update(self, func, *args, **kwargs):
        """Adds a function to the UI update queue."""
        self.ui_queue.put(lambda: func(*args, **kwargs))

    def _run_shadowsocks_thread(self):
        """Threaded function to start the shadowsocks process."""
        self._queue_ui_update(self.update_status, "Connecting...", "#00C0FF")
        try:
            command = [
                sys.executable, "-m", "shadowsocks", "-s", self.entry_server.get(),
                "-p", self.entry_port.get(), "-k", self.entry_password.get(),
                "-m", self.entry_method.get(), "-l", self.entry_local_port.get()
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.ss_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               universal_newlines=True, startupinfo=startupinfo)
            
            self._queue_ui_update(self.update_status, "Connected", "#32CD32")
            self._queue_ui_update(self.update_info_box, (
                "The Shadowsocks client is connected and running.\n\n"
                f"SOCKS5 proxy at: 127.0.0.1:{self.entry_local_port.get()}"
            ))
            self.start_latency_check()
        except FileNotFoundError:
            self._queue_ui_update(self.update_status, "Error: Module not found", "#FF5733")
            self._queue_ui_update(self.update_info_box, "Please install with: pip install shadowsocks")
            self.ss_process = None
        except Exception as e:
            self._queue_ui_update(self.update_status, f"Error: {e}", "#FF5733")
            self._queue_ui_update(self.update_info_box, f"An unexpected error occurred: {e}")
            self.ss_process = None

    def connect_proxy(self):
        """Starts the shadowsocks proxy in a new thread."""
        if self.ss_process and self.ss_process.poll() is None:
            return
        
        try:
            local_port = int(self.entry_local_port.get())
            if local_port < 1024:
                messagebox.showwarning("Port Error", "Use a port number of 1024 or higher.")
                return
        except ValueError:
            messagebox.showerror("Invalid Port", "The local port must be a valid number.")
            return

        self.save_config()
        threading.Thread(target=self._run_shadowsocks_thread, daemon=True).start()

    def disconnect_proxy(self):
        """Terminates the shadowsocks process."""
        self.latency_running = False
        if self.latency_thread and self.latency_thread.is_alive():
            self.latency_thread.join(timeout=5)
            self.latency_thread = None

        if self.ss_process and self.ss_process.poll() is None:
            try:
                self.ss_process.terminate()
                self.ss_process.wait(timeout=5)
            except (subprocess.TimeoutExpired, Exception) as e:
                print(f"Could not disconnect gracefully, killing process: {e}")
                self.ss_process.kill()
            finally:
                self.ss_process = None

        self.update_status("Disconnected", "#FF5733")
        self.update_info_box("")
        self.update_latency_label("N/A")

    def start_latency_check(self):
        """Starts a background thread for latency checks."""
        if not self.latency_running:
            self.latency_running = True
            self.latency_thread = threading.Thread(target=self._run_latency_check, daemon=True)
            self.latency_thread.start()

    def _run_latency_check(self):
        """Performs periodic latency checks on the server."""
        server = self.entry_server.get()
        if not server:
            self._queue_ui_update(self.update_latency_label, "N/A")
            self.latency_running = False
            return
            
        while self.latency_running:
            try:
                command = ["ping", "-n", "1", server] if os.name == 'nt' else ["ping", "-c", "1", server]
                startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
                if startupinfo:
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                
                result = subprocess.run(command, capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
                
                regex = r"Average = (\d+)ms" if os.name == 'nt' else r"min/avg/max/stddev = [\d.]+/([\d.]+)"
                match = re.search(regex, result.stdout + result.stderr, re.IGNORECASE)

                latency = f"{float(match.group(1)):.0f}ms" if match else "Timeout"
                self._queue_ui_update(self.update_latency_label, latency)
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                self._queue_ui_update(self.update_latency_label, "Failed")
            
            time.sleep(5)

    def update_status(self, text, color):
        """Updates the status label on the UI thread."""
        self.status_label.config(text=f"Status: {text}", foreground=color)

    def update_info_box(self, text):
        """Updates the info box on the UI thread."""
        self.info_label.config(text=text)

    def update_latency_label(self, text):
        """Updates the latency label on the UI thread."""
        self.latency_label.config(text=f"Latency: {text}")

    def _setup_tray_icon(self):
        """Initializes the system tray icon using icon.ico, with a fallback."""
        try:
            image = Image.open("icon.ico")
        except FileNotFoundError:
            print("Warning: Icon file not found. Using a default generated icon.")
            image = Image.new('RGB', (64, 64), color='#1E1E1E')
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 64, 64), fill='#FF5733')

        menu = (
            Item('Connect', self.connect_proxy),
            Item('Disconnect', self.disconnect_proxy),
            Item('Show/Hide', self._toggle_window_visibility),
            Item('Quit', self.quit_app)
        )
        self.tray_icon = Icon("shadowsocks_client", image, "Shadowsocks Client", menu)
        self.tray_icon.run()

    def hide_to_tray(self):
        """Hides the window to the system tray."""
        self.save_config()
        self.root.withdraw()
        
    def _toggle_window_visibility(self, icon, item):
        """Toggles the visibility of the main window."""
        self._queue_ui_update(lambda: self.root.deiconify() if self.root.state() == "withdrawn" else self.root.withdraw())
        if self.root.state() == "withdrawn":
            self._queue_ui_update(self.root.lift)
            self._queue_ui_update(self.root.focus_force)

    def quit_app(self, icon=None, item=None):
        """Quits the application."""
        self.save_config()
        self.disconnect_proxy()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        release_lock()

    def toggle_startup_setting(self):
        """Toggles the system startup setting."""
        is_enabled = self.startup_var.get()
        app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}" --hidden'
        
        if sys.platform.startswith('linux'):
            autostart_dir = os.path.join(os.path.expanduser('~'), '.config', 'autostart')
            desktop_file_path = os.path.join(autostart_dir, 'shadowsocks.desktop')
            try:
                if is_enabled:
                    os.makedirs(autostart_dir, exist_ok=True)
                    with open(desktop_file_path, 'w') as f:
                        f.write(f'[Desktop Entry]\nExec={app_path}\nName=Shadowsocks Client\n')
                elif os.path.exists(desktop_file_path):
                    os.remove(desktop_file_path)
            except (IOError, PermissionError) as e:
                messagebox.showerror("Error", f"Failed to modify autostart file: {e}")
                self.startup_var.set(not is_enabled)
        elif os.name == 'nt':
            run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_WRITE) as key:
                    if is_enabled:
                        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
                    else:
                        winreg.DeleteValue(key, APP_NAME)
            except (WindowsError, PermissionError) as e:
                messagebox.showerror("Error", f"Failed to change Windows startup setting: {e}")
                self.startup_var.set(not is_enabled)
        else:
            messagebox.showwarning("Startup Setting", "This feature is only supported on Windows and Linux.")
            self.startup_var.set(False)
            
        self.save_config()

# --- Main Entry Point ---
if __name__ == "__main__":
    try:
        import shadowsocks
        from pystray import MenuItem as Item, Icon
        from PIL import Image, ImageDraw
        import appdirs
    except ImportError as e:
        messagebox.showerror(
            "Dependency Error",
            f"A required library is not installed: {e.name}\n"
            "Please run: pip install shadowsocks pystray Pillow appdirs"
        )
        sys.exit(1)

    if not acquire_lock():
        messagebox.showinfo("Shadowsocks Client", "The client is already running.")
        sys.exit(0)

    atexit.register(release_lock)

    root = tk.Tk()
    app = ShadowsocksClientApp(root)
    
    if "--hidden" in sys.argv:
        root.withdraw()
    
    root.mainloop()

