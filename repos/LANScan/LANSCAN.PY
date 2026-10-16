import tkinter as tk
from tkinter import ttk
from scapy.all import ARP, sniff, srp, sr, conf, IP, ICMP, Ether
import threading
import socket
from pathlib import Path
from datetime import datetime
import ipaddress
import time
import logging

# Suppress Scapy warnings for a cleaner console
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# ===============================
# Helper functions
# ===============================
def get_hostname(ip_address):
    """Performs a reverse DNS lookup for a given IP."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except (socket.herror, socket.gaierror):
        return "Unknown"

def passive_scan(iface, stop_event, callback, error_callback):
    """Continuously listens for ARP and ICMP packets."""
    try:
        sniff(
            filter="arp or icmp",
            prn=callback,
            store=0,
            stop_filter=lambda _: stop_event.is_set(),
            iface=iface
        )
    except OSError as e:
        error_callback(f"Error: {e}. Check permissions (e.g., run as root/Admin).")
    except Exception as e:
        error_callback(f"Passive sniff stopped unexpectedly: {e}")

def active_scan(iface, stop_event, callback, error_callback):
    """Performs an ARP and ICMP sweep of the local network."""
    try:
        # Determine the network range from the interface's IP
        iface_info = conf.ifaces.data.get(iface)
        if not iface_info or not iface_info.ip:
            error_callback("Error: Interface IP not found.")
            return

        net = ipaddress.IPv4Network(f"{iface_info.ip}/24", strict=False)
        
        # Craft packets for ARP and ICMP
        arp_packet = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=str(net.network_address) + "/24")
        icmp_packet = IP(dst=str(net.network_address) + "/24")/ICMP()
        
        # Send ARP requests and process responses
        ans, unans = srp(arp_packet, timeout=1, verbose=0, iface=iface)
        for sent, received in ans:
            if stop_event.is_set(): return
            callback(received)
        
        # Send ICMP echo requests and process responses
        ans, unans = sr(icmp_packet, timeout=1, verbose=0, iface=iface)
        for sent, received in ans:
            if stop_event.is_set(): return
            callback(received)

    except Exception as e:
        error_callback(f"Active scan failed: {e}")

# ===============================
# GUI
# ===============================
class NetworkMapperGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("LAN Network Mapper")
        self.master.geometry("800x600")
        self.master.configure(bg="#0a192f")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # State variables
        self.devices = {}
        self.device_widgets = {}
        self.device_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.scan_mode = "passive"  # "passive" or "active"
        self.iface_info = self._get_available_interfaces()
        self.selected_iface = None
        
        self._setup_style()
        self._create_widgets()
        self._initialize_scan()
        self.active_copy_button = None # Store the active copy button
        self.last_clicked_ip = None # Store the last clicked IP address for toggling the button

    
    def _setup_style(self):
        """Configures the ttk styles for a sci-fi theme."""
        style = ttk.Style()
        style.theme_create("scifi_theme", parent="alt", settings={
            "TFrame": {"configure": {"background": "#0a192f"}},
            "TLabel": {"configure": {"background": "#0a192f", "foreground": "#64ffda"}},
            "Header.TLabel": {"configure": {"font": ("Consolas", 32, "bold")}},
            "Control.TLabel": {"configure": {"background": "#122a45", "foreground": "#ccd6f6", "font": ("Consolas", 12)}},
            "Status.TLabel": {"configure": {"font": ("Consolas", 12, "italic")}},
            "TCombobox": {"configure": {"fieldbackground": "#1a2c41", "foreground": "#64ffda", "background": "#1a2c41", "font": ("Consolas", 12)}},
            "Device.TFrame": {"configure": {"background": "#1a2c41", "relief": "solid", "borderwidth": 1, "padding": 15}},
            "DeviceHeader.TLabel": {"configure": {"background": "#1a2c41", "foreground": "#64ffda", "font": ("Consolas", 14, "bold")}},
            "DeviceDetail.TLabel": {"configure": {"background": "#1a2c41", "foreground": "#ccd6f6", "font": ("Consolas", 12)}},
            "Control.TButton": {"configure": {"background": "#64ffda", "foreground": "#0a192f", "font": ("Consolas", 12, "bold"), "padding": 5}},
            "Scifi.Vertical.TScrollbar": {"configure": {"troughcolor": "#1a2c41", "background": "#64ffda", "relief": "flat"}},
            "Copy.TButton": {"configure": {"background": "#122a45", "foreground": "#64ffda", "font": ("Consolas", 10), "relief": "flat", "padding": [5, 2]}},
        })
        style.theme_use("scifi_theme")
        style.map("Control.TButton", background=[('active', '#1a2c41')], foreground=[('active', '#64ffda')])
        
    def _create_widgets(self):
        """Creates and packs all the GUI widgets."""
        main_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="LAN Network Mapper", style="Header.TLabel").pack(pady=(0, 20))
        
        control_frame = ttk.Frame(main_frame, style="Control.TFrame", padding="15")
        control_frame.pack(fill=tk.X, pady=10)
        
        # Interface selection and control buttons
        iface_frame = ttk.Frame(control_frame, style="TFrame")
        iface_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(iface_frame, text="Network Interface:", style="Control.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.iface_combobox = ttk.Combobox(iface_frame, width=40, state="readonly", style="TCombobox")
        self.iface_combobox.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.iface_combobox.bind("<<ComboboxSelected>>", self.on_interface_selected)

        # Action buttons
        button_frame = ttk.Frame(control_frame, style="TFrame")
        button_frame.pack(fill=tk.X)
        
        self.passive_button = ttk.Button(button_frame, text="Passive Scan", command=self.start_passive_scan, style="Control.TButton")
        self.passive_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.active_button = ttk.Button(button_frame, text="Active Scan", command=self.start_active_scan, style="Control.TButton")
        self.active_button.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)

        self.save_button = ttk.Button(button_frame, text="Save to File", command=self.save_to_file, style="Control.TButton")
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.X, expand=True)

        self.status_label = ttk.Label(main_frame, text="Initializing...", style="Status.TLabel")
        self.status_label.pack(pady=10)

        self.canvas = tk.Canvas(main_frame, background="#0e1a2f", highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview, style="Scifi.Vertical.TScrollbar")
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")

        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=(0,20))
        self.scrollbar.pack(side="right", fill="y", pady=(0,20))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.master.bind("<Configure>", lambda e: self.master.after(100, lambda: self.canvas.itemconfig(self.canvas_frame_id, width=self.canvas.winfo_width())))
        
        # Bind mouse wheel scrolling to the main window
        self.master.bind("<MouseWheel>", self._on_mouse_scroll)
        # Bindings for macOS
        self.master.bind("<Button-4>", self._on_mouse_scroll)
        self.master.bind("<Button-5>", self._on_mouse_scroll)

    def _on_mouse_scroll(self, event):
        """Handles mouse wheel scrolling across the entire window."""
        # For Windows and most Linux
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # For macOS
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def _initialize_scan(self):
        """Populates interfaces and starts the initial passive scan."""
        if self.iface_info:
            iface_list = [info['display_name'] for info in self.iface_info.values()]
            self.iface_combobox['values'] = iface_list
            self.selected_iface = next(iter(self.iface_info))
            self.iface_combobox.set(self.iface_info[self.selected_iface]['display_name'])
            self.clear_device_list()
            self.start_passive_scan()
        else:
            self.iface_combobox.config(state="disabled")
            self.status_label.config(text="Error: No functional network interfaces found. Try running as administrator.")

    def _get_available_interfaces(self):
        """Returns a dict of all available interfaces with an IP address."""
        return {
            iface_name: {"ip": iface.ip, "display_name": f"{iface_name} ({iface.ip})"}
            for iface_name, iface in conf.ifaces.data.items() if iface.ip
        }
    
    def on_interface_selected(self, event):
        """Stops the current scan and restarts it on the new interface."""
        selected_display_name = self.iface_combobox.get()
        new_iface = next(
            (name for name, info in self.iface_info.items() if info['display_name'] == selected_display_name),
            None
        )
        if new_iface and new_iface != self.selected_iface:
            self.selected_iface = new_iface
            self.stop_scan()
            self.clear_device_list()
            self.master.after(100, self.start_scan)

    def start_scan(self):
        """Starts the appropriate scan based on the current mode."""
        self.stop_event.clear()
        
        if self.scan_mode == "passive":
            self.status_label.config(text=f"Passive scanning started on {self.iface_info[self.selected_iface]['display_name']}...")
            self.scan_thread = threading.Thread(target=passive_scan, 
                                                args=(self.selected_iface, self.stop_event, self.handle_packet, self.handle_scan_error),
                                                daemon=True)
            self.scan_thread.start()
        elif self.scan_mode == "active":
            self.status_label.config(text=f"Active scanning started on {self.iface_info[self.selected_iface]['display_name']}... This may take a moment.")
            self.scan_thread = threading.Thread(target=active_scan,
                                                args=(self.selected_iface, self.stop_event, self.handle_packet, self.handle_scan_error),
                                                daemon=True)
            self.scan_thread.start()
            self.master.after(100, self._check_active_scan_completion)

    def _check_active_scan_completion(self):
        """Checks if the active scan thread is still running."""
        if self.scan_thread and self.scan_thread.is_alive():
            self.master.after(500, self._check_active_scan_completion)
        else:
            self.status_label.config(text=f"Active scan completed. Found {len(self.devices)} devices.")
    
    def start_passive_scan(self):
        self.scan_mode = "passive"
        self.stop_scan()
        self.start_scan()

    def start_active_scan(self):
        self.scan_mode = "active"
        self.stop_scan()
        self.start_scan()
        
    def stop_scan(self):
        """Sets the event to stop the sniffing thread."""
        self.stop_event.set()
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=1)
            
    def handle_scan_error(self, error_message):
        """Updates the GUI with an error message from the scan thread."""
        self.master.after(0, lambda: self.status_label.config(text=error_message))
        self.stop_scan()

    def handle_packet(self, packet):
        """Processes ARP and ICMP packets."""
        ip = None
        mac = None
        if packet.haslayer(ARP):
            ip = packet.psrc
            mac = packet.hwsrc
        elif packet.haslayer(IP) and (packet.haslayer(ICMP) or packet.haslayer(Ether)):
            ip = packet[IP].src
        
        if ip:
            self._add_or_update_device(ip, mac)
    
    def _add_or_update_device(self, ip, mac):
        """Adds or updates a device in the data structure and GUI."""
        with self.device_lock:
            if ip not in self.devices or (mac and self.devices[ip].get("mac") != mac):
                if ip not in self.devices:
                    self.devices[ip] = {"ip": ip, "mac": mac, "hostname": get_hostname(ip)}
                elif mac:
                    self.devices[ip]["mac"] = mac
                
                self.master.after(0, lambda: self._update_device_card(ip))
                
    def _update_device_card(self, ip):
        """Creates or updates the GUI card for a device."""
        if ip not in self.devices:
            return

        device = self.devices[ip]
        if ip in self.device_widgets:
            widgets = self.device_widgets[ip]
            widgets["ip"].config(text=f"IP Address: {device['ip']}")
            widgets["hostname"].config(text=f"Hostname: {device['hostname']}")
            mac_text = f"MAC Address: {device['mac']}" if device['mac'] else "MAC Address: N/A"
            widgets["mac"].config(text=mac_text)
        else:
            card = ttk.Frame(self.scrollable_frame, style="Device.TFrame")
            card.pack(fill="x", padx=10, pady=5)
            # Bind the click event to call the toggle copy option
            card.bind("<Button-1>", lambda e, ip_addr=ip: self._toggle_copy_option(ip_addr))

            # Reordered labels and adjusted padding for better spacing
            labels = {
                "ip": ttk.Label(card, text=f"IP Address: {device['ip']}", style="DeviceHeader.TLabel"),
                "hostname": ttk.Label(card, text=f"Hostname: {device['hostname']}", style="DeviceDetail.TLabel"),
                "mac": ttk.Label(card, text=f"MAC Address: {device['mac'] or 'N/A'}", style="DeviceDetail.TLabel")
            }
            labels["ip"].pack(anchor="w", padx=(10, 0), pady=(5, 2))  # Added top padding here
            labels["hostname"].pack(anchor="w", padx=(10, 0), pady=(0, 2))
            labels["mac"].pack(anchor="w", padx=(10, 0), pady=(0, 5))
            
            # Also bind the click event for the labels inside the card
            for label in labels.values():
                label.bind("<Button-1>", lambda e, ip_addr=ip: self._toggle_copy_option(ip_addr))

            self.device_widgets[ip] = {"frame": card, **labels}
        
        if self.scan_mode == "passive":
            self.status_label.config(text=f"Passive scan active. Found {len(self.devices)} devices.")

    def _toggle_copy_option(self, ip):
        """Toggles the copy button for the selected device."""
        # Destroy any existing copy button regardless of which device it belongs to
        if self.active_copy_button and self.active_copy_button.winfo_exists():
            self.active_copy_button.destroy()

        # Check if the device already has a copy button
        if hasattr(self, 'last_clicked_ip') and self.last_clicked_ip == ip:
            # If the same device is clicked again, just remove the button
            self.last_clicked_ip = None
            return

        card_frame = self.device_widgets[ip]['frame']
        
        copy_button = ttk.Button(
            card_frame,
            text="Copy MAC",
            command=lambda: self.copy_to_clipboard(self.devices[ip]['mac']),
            style="Copy.TButton"
        )
        copy_button.pack(side="right", padx=10, pady=5)
        self.active_copy_button = copy_button
        self.last_clicked_ip = ip
        
    def copy_to_clipboard(self, text):
        """Copies text to the clipboard."""
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self.status_label.config(text=f"Copied '{text}' to clipboard!")
        
    def save_to_file(self):
        """Saves detected devices to a text file."""
        if not self.devices:
            self.status_label.config(text="Error: No devices to save.")
            return

        try:
            documents_path = Path.home() / "Documents"
            documents_path.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{self.scan_mode}_scan_results_{timestamp}.txt"
            file_path = documents_path / filename

            with open(file_path, "w") as f:
                f.write(f"LAN Network Mapper - {self.scan_mode.capitalize()} Scan Results ({self.iface_info[self.selected_iface]['display_name']})\n")
                f.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for ip, device_info in sorted(self.devices.items()):
                    f.write(f"IP: {device_info['ip']}\n")
                    f.write(f"MAC: {device_info['mac'] or 'N/A'}\n")
                    f.write(f"Hostname: {device_info['hostname']}\n")
                    f.write("-" * 20 + "\n")
            
            self.status_label.config(text=f"Successfully saved scan results to: {file_path}")
        except Exception as e:
            self.status_label.config(text=f"Error: Could not save file. {e}")

    def clear_device_list(self):
        """Clears all device widgets and data."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.devices.clear()
        self.device_widgets.clear()
        self.status_label.config(text="")

    def on_closing(self):
        """Stops the scan thread and closes the application."""
        self.stop_scan()
        self.master.destroy()

# ===============================
# Main
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMapperGUI(root)
    root.mainloop()
