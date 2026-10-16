import sys
import os
import ctypes
import traceback
import queue

# --- ERROR HANDLING UTILS ---
def show_critical_error(title, msg):
    """ Shows a native Windows message box for critical errors if GUI fails """
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10)
    except:
        print(f"CRITICAL ERROR: {title}\n{msg}")

# --- IMPORTS ---
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    import time
    import socket
    import json
    from datetime import datetime
except Exception as e:
    show_critical_error("Import Error", f"Failed to load standard libraries.\nError: {e}")
    sys.exit(1)

# Check for 3rd party dependencies specifically
try:
    import psutil
    import requests
except ImportError as e:
    show_critical_error("Missing Dependencies", 
                        f"A required library is missing: {e.name}\n\n"
                        "Please install them by running:\n"
                        "pip install psutil requests")
    sys.exit(1)

# --- CONFIGURATION & STYLING ---
THEME = {
    "bg": "#050505",           # Void Black
    "fg": "#00FF41",           # Matrix Green
    "fg_dim": "#008F11",       # Dim Green
    "accent": "#003B00",       # Dark Green Backgrounds
    "highlight": "#D3D3D3",    # White/Grey for headers
    "alert": "#FF3333",        # Red for termination
    "cyan": "#00FFFF",         # Cyan for external IPs
    "font_main": ("Consolas", 10),
    "font_header": ("Consolas", 12, "bold"),
    "font_mono": ("Courier New", 9)
}

class NetMatrixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NET_MATRIX // SYSTEM_OVERWATCH")
        self.root.geometry("1200x700") 
        self.root.configure(bg=THEME["bg"])
        
        # Data storage
        self.connections_cache = []
        self.selected_pid = None
        self.paused = False
        
        # GeoIP Cache & Worker
        self.ip_cache = {}      # Stores {ip: country_code}
        self.ip_queue = queue.Queue()
        
        # Sorting State
        self.sort_col = "pid"
        self.sort_reverse = False
        
        # UI Elements init
        self.console_text = None
        self.console_queue = []
        
        self._setup_styles()
        self._build_ui()
        self._build_context_menu()
        
        # Start background monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start GeoIP worker thread
        self.geoip_thread = threading.Thread(target=self._geoip_worker, daemon=True)
        self.geoip_thread.start()
        
        # Start processing the console queue
        self._process_console_queue()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", 
                        background=THEME["bg"], 
                        foreground=THEME["fg"], 
                        fieldbackground=THEME["bg"],
                        font=THEME["font_main"],
                        rowheight=25,
                        borderwidth=0)
        
        style.configure("Treeview.Heading", 
                        background=THEME["accent"], 
                        foreground=THEME["highlight"], 
                        font=THEME["font_header"],
                        relief="flat")
        
        style.map("Treeview", 
                  background=[('selected', THEME["fg_dim"])], 
                  foreground=[('selected', 'white')])

        style.configure("Vertical.TScrollbar", 
                        background=THEME["bg"], 
                        troughcolor=THEME["accent"],
                        arrowcolor=THEME["fg"])

    def _build_ui(self):
        top_frame = tk.Frame(self.root, bg=THEME["bg"], pady=10, padx=10)
        top_frame.pack(fill="x")
        
        # Header / Title
        title_lbl = tk.Label(top_frame, text="[ ACTIVE_CONNECTIONS_MONITOR ]", 
                             bg=THEME["bg"], fg=THEME["cyan"], font=("Consolas", 16, "bold"))
        title_lbl.pack(side="left")
        
        # Search Filter
        search_frame = tk.Frame(top_frame, bg=THEME["bg"])
        search_frame.pack(side="right", padx=10)
        
        tk.Label(search_frame, text="FILTER_MATRIX:", bg=THEME["bg"], fg=THEME["fg_dim"], font=THEME["font_mono"]).pack(side="left", padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                     bg=THEME["accent"], fg=THEME["fg"], 
                                     insertbackground=THEME["fg"], font=THEME["font_mono"], width=20)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.status_lbl = tk.Label(top_frame, text="STATUS: SCANNING...", 
                                   bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_main"])
        self.status_lbl.pack(side="right", padx=15)

        # List Area
        list_frame = tk.Frame(self.root, bg=THEME["accent"], bd=2, relief="sunken")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("pid", "proto", "l_addr", "r_addr", "country", "status", "process")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Column Headers
        headers = [
            ("pid", "PID"), 
            ("proto", "PROTO"), 
            ("l_addr", "LOCAL_ADDR"), 
            ("r_addr", "REMOTE_ADDR"), 
            ("country", "CNTRY"), 
            ("status", "STATE"), 
            ("process", "PROCESS_NAME")
        ]
        
        for col, text in headers:
            self.tree.heading(col, text=text, command=lambda c=col: self._on_header_click(c))
        
        self.tree.column("pid", width=60, anchor="center")
        self.tree.column("proto", width=60, anchor="center")
        self.tree.column("l_addr", width=150, anchor="w")
        self.tree.column("r_addr", width=150, anchor="w")
        self.tree.column("country", width=60, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("process", width=200, anchor="w")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._show_context_menu) # Right click

        # Action Panel
        action_frame = tk.Frame(self.root, bg=THEME["bg"], pady=10, padx=10)
        action_frame.pack(fill="x")
        
        btn_style = {"bg": THEME["accent"], "fg": THEME["fg"], "activebackground": THEME["fg"], "activeforeground": "black", "bd": 1, "relief": "solid", "font": THEME["font_header"], "width": 15}
        
        self.btn_investigate = tk.Button(action_frame, text="INVESTIGATE [IP]", command=self._investigate_connection, **btn_style)
        self.btn_investigate.pack(side="left", padx=5)
        
        self.btn_terminate = tk.Button(action_frame, text="TERMINATE [PID]", command=self._terminate_connection, **btn_style)
        self.btn_terminate.pack(side="left", padx=5)
        self.btn_terminate.config(fg=THEME["alert"])
        
        self.btn_pause = tk.Button(action_frame, text="PAUSE STREAM", command=self._toggle_pause, **btn_style)
        self.btn_pause.pack(side="right", padx=5)

        # Console
        console_frame = tk.LabelFrame(self.root, text="DATA_LOG // INTELLIGENCE", bg=THEME["bg"], fg=THEME["highlight"], bd=1, relief="solid", font=THEME["font_mono"])
        console_frame.pack(fill="x", padx=10, pady=10, ipady=5)
        
        try:
            self.console_text = tk.Text(console_frame, height=8, bg="black", fg=THEME["fg"], 
                                        font=THEME["font_mono"], bd=0, state="disabled")
            self.console_text.pack(fill="both", padx=5, pady=5)
        except Exception as e:
            print(f"Error creating console: {e}")
            self.console_text = None
        
        self.log_message("SYSTEM INITIALIZED...")
        self.log_message("WAITING FOR NETWORK SIGNATURES...")

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=THEME["bg"], fg=THEME["fg"], activebackground=THEME["fg_dim"], activeforeground="white")
        self.context_menu.add_command(label="COPY REMOTE IP", command=lambda: self._copy_to_clipboard("ip"))
        self.context_menu.add_command(label="COPY PID", command=lambda: self._copy_to_clipboard("pid"))
        self.context_menu.add_command(label="COPY PROCESS NAME", command=lambda: self._copy_to_clipboard("process"))

    def _monitor_loop(self):
        while True:
            if not self.paused:
                try:
                    conns = psutil.net_connections(kind='inet')
                    formatted_data = []
                    for c in conns:
                        try:
                            proc = psutil.Process(c.pid)
                            proc_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            proc_name = "UNKNOWN/SYSTEM"
                            
                        l_ip = f"{c.laddr.ip}:{c.laddr.port}"
                        r_ip = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ":::"
                        
                        # Determine Country
                        country = "--"
                        if c.raddr:
                            ip = c.raddr.ip
                            if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
                                country = "LOC"
                            else:
                                if ip in self.ip_cache:
                                    country = self.ip_cache[ip]
                                else:
                                    self.ip_cache[ip] = "..."
                                    self.ip_queue.put(ip)
                                    country = "..."

                        formatted_data.append((
                            c.pid,
                            "TCP" if c.type == socket.SOCK_STREAM else "UDP",
                            l_ip,
                            r_ip,
                            country,
                            c.status,
                            proc_name
                        ))
                    
                    self.root.after(0, self._update_tree, formatted_data)
                    
                except Exception as e:
                    print(f"Error scanning: {e}")
            
            time.sleep(2)

    def _geoip_worker(self):
        while True:
            try:
                ip = self.ip_queue.get()
                if ip:
                    try:
                        response = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            self.ip_cache[ip] = data.get("countryCode", "UNK")
                        else:
                            self.ip_cache[ip] = "ERR"
                    except:
                        self.ip_cache[ip] = "ERR"
                    time.sleep(1.5) 
            except Exception as e:
                print(f"GeoIP Worker Error: {e}")

    def _on_header_click(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        
        # Trigger resort
        if self.connections_cache:
            self._update_tree(self.connections_cache)

    def _on_search(self, event=None):
        """ Triggered when user types in the search bar """
        if self.connections_cache:
            self._update_tree(self.connections_cache)

    def _update_tree(self, new_data):
        self.connections_cache = new_data
        
        # 1. Filter Data
        search_query = self.search_var.get().lower()
        filtered_data = []
        if search_query:
            for item in new_data:
                # Check PID, Remote IP, Process Name
                # item structure: (pid, proto, l_addr, r_addr, country, status, process)
                pid_str = str(item[0])
                r_ip = str(item[3]).lower()
                proc = str(item[6]).lower()
                
                if search_query in pid_str or search_query in r_ip or search_query in proc:
                    filtered_data.append(item)
        else:
            filtered_data = list(new_data) # Copy list

        # 2. Sort Data
        col_map = {"pid": 0, "proto": 1, "l_addr": 2, "r_addr": 3, "country": 4, "status": 5, "process": 6}
        idx = col_map.get(self.sort_col, 0)
        
        def sort_key(item):
            val = item[idx]
            if val is None: return 0 if idx == 0 else ""
            if isinstance(val, str):
                return val.lower()
            return val
            
        filtered_data.sort(key=sort_key, reverse=self.sort_reverse)

        # 3. Preserve Selection
        # FIX: Rely on self.selected_pid for state persistence and cast to string for comparison
        target_pid = str(self.selected_pid) if self.selected_pid is not None else None

        # 4. Render
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        found_selection = None
        for item in filtered_data:
            row_id = self.tree.insert("", "end", values=item)
            # Compare strings to handle potential int vs str type mismatch from Tkinter
            if target_pid and str(item[0]) == target_pid:
                found_selection = row_id

        if found_selection:
            self.tree.selection_set(found_selection)
            self.tree.see(found_selection)
            
        count = len(filtered_data)
        total = len(new_data)
        if search_query:
            self.status_lbl.config(text=f"STATUS: FILTERED [{count}/{total}]")
        else:
            self.status_lbl.config(text=f"STATUS: MONITORING [{count} ACTIVE LINES]")

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_pid = item['values'][0]
            self.selected_r_ip = item['values'][3]
            self.selected_proc = item['values'][6]

    def _show_context_menu(self, event):
        """ Display the right-click menu """
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _copy_to_clipboard(self, mode):
        if not hasattr(self, 'selected_pid') or not self.selected_pid:
            return
            
        val = ""
        if mode == "ip":
            val = self.selected_r_ip.split(":")[0]
        elif mode == "pid":
            val = str(self.selected_pid)
        elif mode == "process":
            val = self.selected_proc
            
        self.root.clipboard_clear()
        self.root.clipboard_append(val)
        self.log_message(f"COPIED TO BUFFER: {val}", color=THEME["highlight"])

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="RESUME STREAM", fg=THEME["cyan"])
            self.status_lbl.config(text="STATUS: PAUSED [FROZEN]")
        else:
            self.btn_pause.config(text="PAUSE STREAM", fg=THEME["fg"])

    def _terminate_connection(self):
        if not self.selected_pid:
            self.log_message("ERROR: NO TARGET SELECTED.", color=THEME["alert"])
            return

        try:
            pid = int(self.selected_pid)
            if pid == 0:
                self.log_message("ERROR: CANNOT TERMINATE SYSTEM KERNEL.", color=THEME["alert"])
                return

            proc = psutil.Process(pid)
            name = proc.name()
            
            confirm = messagebox.askyesno("TERMINATION CONFIRMATION", 
                                          f"Are you sure you want to kill process:\n{name} (PID: {pid})?")
            if confirm:
                proc.terminate()
                self.log_message(f"COMMAND EXECUTED: PID {pid} [{name}] TERMINATED.", color=THEME["alert"])
                self.root.after(100, lambda: self._update_tree([])) 
        except psutil.NoSuchProcess:
            self.log_message("ERROR: TARGET ALREADY VANISHED.", color=THEME["alert"])
        except psutil.AccessDenied:
            self.log_message("ERROR: ACCESS DENIED. ELEVATION REQUIRED.", color=THEME["alert"])
        except Exception as e:
            self.log_message(f"ERROR: {str(e)}", color=THEME["alert"])

    def _investigate_connection(self):
        if not hasattr(self, 'selected_r_ip') or not self.selected_r_ip or ":::" in self.selected_r_ip:
            self.log_message("ERROR: INVALID OR LOCAL TARGET.", color=THEME["alert"])
            return

        ip = self.selected_r_ip.split(":")[0]
        if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
            self.log_message(f"TARGET {ip} IS INTERNAL/LAN.", color=THEME["cyan"])
            return

        self.log_message(f"INITIATING TRACE ON {ip}...", color=THEME["cyan"])
        threading.Thread(target=self._fetch_geoip, args=(ip,), daemon=True).start()

    def _fetch_geoip(self, ip):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    info = (f"TRACE COMPLETE // {ip}\n"
                            f"  > ORG: {data.get('org', 'Unknown')}\n"
                            f"  > ISP: {data.get('isp', 'Unknown')}\n"
                            f"  > LOC: {data.get('city', '?')}, {data.get('country', '?')}\n"
                            f"  > LAT/LON: {data.get('lat')}, {data.get('lon')}")
                    self.log_message(info)
                else:
                    self.log_message(f"TRACE FAILED: {data.get('message')}", color=THEME["alert"])
            else:
                self.log_message("TRACE ERROR: API UNREACHABLE", color=THEME["alert"])
        except Exception as e:
            self.log_message(f"TRACE EXCEPTION: {str(e)}", color=THEME["alert"])

    def log_message(self, message, color=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        final_msg = f"[{timestamp}] {message}\n"
        if hasattr(self, 'console_queue'):
            self.console_queue.append((final_msg, color if color else THEME["fg"]))

    def _process_console_queue(self):
        if self.console_queue and self.console_text:
            msg, color = self.console_queue.pop(0)
            try:
                self.console_text.configure(state="normal")
                tag_name = f"color_{len(self.console_text.get('1.0', 'end'))}"
                self.console_text.tag_config(tag_name, foreground=color)
                self.console_text.insert("end", msg, tag_name)
                self.console_text.see("end")
                self.console_text.configure(state="disabled")
            except:
                pass
        self.root.after(100, self._process_console_queue)

def is_admin():
    try:
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.getuid() == 0
    except:
        return False

if __name__ == "__main__":
    try:
        if is_admin():
            root = tk.Tk()
            app = NetMatrixApp(root)
            root.mainloop()
        else:
            script_path = os.path.abspath(sys.argv[0])
            if sys.platform == 'win32':
                params = [script_path] + sys.argv[1:]
                cmd_params = " ".join([f'"{arg}"' for arg in params])
                ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd_params, None, 1)
                if int(ret) <= 32:
                    show_critical_error("Elevation Failed", "Failed to elevate privileges.")
            else:
                os.execvp('sudo', ['sudo', sys.executable, script_path] + sys.argv[1:])
            sys.exit()
    except Exception as e:
        show_critical_error("Runtime Crash", f"An unexpected error occurred:\n{traceback.format_exc()}")
        input("Press Enter to exit...")