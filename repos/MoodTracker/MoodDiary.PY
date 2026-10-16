import json
import os
import datetime
import time
import hashlib
import csv
import calendar
import threading
import tkinter as tk
import itertools
from tkinter import ttk, simpledialog, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import numpy as np

# Files
DATA_FILE = "mood_tracker_data.json"
CONFIG_FILE = "mood_tracker_config.json"

class MoodTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mood Tracker")
        self.root.geometry("1100x850")
        
        # --- State Variables ---
        self.dark_mode = False
        self.current_user_password_hash = None
        self.note_char_limit = 50 
        
        # Matplotlib Annotation references
        self.annot = None
        self.annot_map = None
        
        # --- Config & Data Loading ---
        self.load_config()
        self.data = self.load_data()
        self.migrate_data_structure() 
        
        # --- UI Setup ---
        self.setup_colors()
        self.setup_fonts()
        self.setup_styles()
        
        # --- Auth Check ---
        if self.current_user_password_hash:
            self.show_login_screen()
        else:
            self.build_main_app()

    def setup_colors(self):
        if self.dark_mode:
            self.colors = {
                "bg": "#1f2937", "card_bg": "#374151", 
                "text_primary": "#f9fafb", "text_secondary": "#d1d5db",
                "accent": "#818cf8", "accent_hover": "#6366f1",
                "success": "#34d399", "danger": "#f87171", "border": "#4b5563"
            }
        else:
            self.colors = {
                "bg": "#f0f2f5", "card_bg": "#ffffff",
                "text_primary": "#1f2937", "text_secondary": "#6b7280",
                "accent": "#6366f1", "accent_hover": "#4f46e5",
                "success": "#10b981", "danger": "#ef4444", "border": "#e5e7eb"
            }
        self.root.configure(bg=self.colors["bg"])

    def setup_fonts(self):
        self.fonts = {
            "h1": ("Segoe UI", 20, "bold"),
            "h2": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 11),
            "label": ("Segoe UI", 10, "bold"),
            "small": ("Segoe UI", 9)
        }

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure("Main.TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        
        self.style.configure("H1.TLabel", background=self.colors["bg"], foreground=self.colors["text_primary"], font=self.fonts["h1"])
        self.style.configure("H2.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_primary"], font=self.fonts["h2"])
        self.style.configure("Body.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_secondary"], font=self.fonts["body"])
        self.style.configure("BgBody.TLabel", background=self.colors["bg"], foreground=self.colors["text_primary"], font=self.fonts["body"])
        self.style.configure("Small.TLabel", background=self.colors["bg"], foreground=self.colors["text_secondary"], font=self.fonts["small"])

        # Checkbutton
        self.style.configure("TCheckbutton", background=self.colors["card_bg"], foreground=self.colors["text_primary"], font=self.fonts["body"])

        # Buttons
        self.style.configure("Accent.TButton", background=self.colors["accent"], foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
        self.style.map("Accent.TButton", background=[("active", self.colors["accent_hover"])])

        self.style.configure("Secondary.TButton", background=self.colors["card_bg"], foreground=self.colors["accent"], font=("Segoe UI", 10), borderwidth=1, bordercolor=self.colors["accent"], padding=6)
        
        self.style.configure("Danger.TButton", background=self.colors["card_bg"], foreground=self.colors["danger"], font=("Segoe UI", 10), borderwidth=1, bordercolor=self.colors["danger"], padding=6)
        self.style.map("Danger.TButton", background=[("active", "#fee2e2" if not self.dark_mode else "#7f1d1d")])

        # Slider
        self.style.configure("Horizontal.TScale", background=self.colors["accent"], troughcolor=self.colors["border"], bordercolor=self.colors["card_bg"], lightcolor=self.colors["accent"], darkcolor=self.colors["accent"])

        # Notebook
        self.style.configure("TNotebook", background=self.colors["bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        # Added 'width=25' and 'anchor="center"' to enforce equal size and centering
        self.style.configure("TNotebook.Tab", padding=[20, 10], width=25, anchor="center", font=("Segoe UI", 11, "bold"), background=self.colors["bg"], foreground=self.colors["text_secondary"])
        
        # Explicitly map padding to prevent shrinking/jitter on selection
        self.style.map("TNotebook.Tab", 
            background=[("selected", self.colors["card_bg"])], 
            foreground=[("selected", self.colors["accent"])],
            padding=[("selected", [20, 10])] 
        )

    # --- Data & Config Management ---

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.dark_mode = config.get("dark_mode", False)
                self.current_user_password_hash = config.get("password_hash", None)

    def save_config(self):
        config = {
            "dark_mode": self.dark_mode,
            "password_hash": self.current_user_password_hash
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {
                "kpis": [
                    {"name": "Happiness", "type": "slider"},
                    {"name": "Energy", "type": "slider"},
                    {"name": "Sleep Quality", "type": "slider"},
                    {"name": "Exercise", "type": "tag"},
                    {"name": "Meditation", "type": "tag"},
                    {"name": "Socializing", "type": "tag"}
                ],
                "history": []
            }
        with open(DATA_FILE, 'r') as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def migrate_data_structure(self):
        new_kpis = []
        for kpi in self.data['kpis']:
            if isinstance(kpi, str):
                new_kpis.append({"name": kpi, "type": "slider"})
            else:
                new_kpis.append(kpi)
        self.data['kpis'] = new_kpis

    def get_today_entry(self):
        today = datetime.date.today().isoformat()
        for entry in self.data['history']:
            if entry['date'] == today:
                return entry
        return None
    
    def get_daily_average_mood(self, entry):
        slider_metrics = [k['name'] for k in self.data['kpis'] if k.get('type') == 'slider']
        scores = [entry['scores'].get(name, 0) for name in slider_metrics if name in entry['scores']]
        
        if not scores:
            return -1 
        
        return sum(scores) / len(scores)

    # --- Authentication ---

    def show_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        frame = ttk.Frame(self.root, style="Main.TFrame")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="🔒 Locked", style="H1.TLabel").pack(pady=20)
        
        self.password_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.password_var, show="*", font=self.fonts["h2"])
        entry.pack(pady=10, padx=20)
        entry.focus_set()
        
        btn = ttk.Button(frame, text="Unlock", style="Accent.TButton", command=self.check_password)
        btn.pack(pady=20, fill='x')
        self.root.bind('<Return>', lambda e: self.check_password())

    def check_password(self):
        password = self.password_var.get()
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if hashed == self.current_user_password_hash:
            self.root.unbind('<Return>')
            self.build_main_app()
        else:
            messagebox.showerror("Error", "Incorrect Password")

    # --- Main Application Builder ---

    def build_main_app(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=20)
        
        self.tab_input = ttk.Frame(self.notebook, style="Main.TFrame")
        self.tab_history = ttk.Frame(self.notebook, style="Main.TFrame")
        self.tab_insights = ttk.Frame(self.notebook, style="Main.TFrame")
        self.tab_settings = ttk.Frame(self.notebook, style="Main.TFrame")

        self.notebook.add(self.tab_input, text="  Today's Mood  ")
        self.notebook.add(self.tab_history, text="  History Trends  ")
        self.notebook.add(self.tab_insights, text="  Insights & Heatmap  ")
        self.notebook.add(self.tab_settings, text="  Settings  ")
        
        self.sliders = {}
        self.checkboxes = {}
        self.check_vars = {}
        self.score_labels = {}
        self.note_text_widget = None
        self.char_count_label = None

        self.build_input_tab()
        self.build_history_tab()
        self.build_insights_tab()
        self.build_settings_tab()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # --- Tab 1: Input ---

    def build_input_tab(self):
        for widget in self.tab_input.winfo_children(): widget.destroy()

        header_frame = ttk.Frame(self.tab_input, style="Main.TFrame")
        header_frame.pack(fill='x', pady=(10, 20), padx=10)
        
        date_str = datetime.date.today().strftime('%A, %B %d')
        ttk.Label(header_frame, text=f"How are you feeling this {date_str}?", style="H1.TLabel").pack(side='left')

        # --- Filter Metrics ---
        slider_kpis = [k for k in self.data['kpis'] if k.get('type') == 'slider']
        tag_kpis = [k for k in self.data['kpis'] if k.get('type') == 'tag']
        
        # --- Scrollable Area for SLIDERS (Main Content) ---
        canvas = tk.Canvas(self.tab_input, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_input, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Main.TFrame")

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        frame_window_id = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(frame_window_id, width=event.width if 'event' in locals() else e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        today_entry = self.get_today_entry()
        current_scores = today_entry['scores'] if today_entry else {}
        current_note = today_entry.get('note', '') if today_entry else ""

        self.sliders = {}
        self.checkboxes = {}
        self.check_vars = {}
        self.score_labels = {}

        # Render SLIDER Metrics
        for kpi_data in slider_kpis:
            name = kpi_data['name']

            card = ttk.Frame(self.scrollable_frame, style="Card.TFrame", padding=20)
            card.pack(fill='x', pady=8, padx=5)
            
            top_row = ttk.Frame(card, style="Card.TFrame")
            top_row.pack(fill='x', pady=(0, 10))
            ttk.Label(top_row, text=name, style="H2.TLabel").pack(side='left')

            val = current_scores.get(name, 5.0)

            # Render Slider specific controls
            color = self.get_score_color(val)
            val_lbl = ttk.Label(top_row, text=f"{val:.1f}", font=("Segoe UI", 18, "bold"), foreground=color, background=self.colors["card_bg"])
            val_lbl.pack(side='right')
            self.score_labels[name] = val_lbl
            
            scale = ttk.Scale(card, from_=0, to=10, orient='horizontal', command=lambda v, k=name: self.update_label(k, v))
            scale.set(val)
            scale.pack(fill='x', expand=True)
            self.sliders[name] = scale

        # --- Footer (Save, Management Buttons, Note, Tags) ---
        footer_frame = ttk.Frame(self.tab_input, style="Main.TFrame")
        footer_frame.pack(fill='x', pady=20, padx=10)
        
        btn_save = ttk.Button(footer_frame, text="Save Daily Log", style="Accent.TButton", command=self.save_today)
        btn_save.pack(fill='x', padx=100)

        # Management Buttons
        manage_frame = ttk.Frame(footer_frame, style="Main.TFrame")
        manage_frame.pack(pady=(15, 0))
        ttk.Button(manage_frame, text="- Remove Metric", style="Danger.TButton", command=self.remove_kpi_dialog).pack(fill='x', pady=5)
        ttk.Button(manage_frame, text="+ Add Metric", style="Secondary.TButton", command=self.add_kpi_dialog).pack(fill='x', pady=5)
        
        # --- Note Section with LIMITER ---
        note_frame = ttk.Frame(footer_frame, style="Main.TFrame")
        note_frame.pack(fill='x', pady=(20, 10))
        ttk.Label(note_frame, text="Daily Note / Reflection:", style="BgBody.TLabel").pack(anchor="center")
        
        self.note_text_widget = tk.Text(note_frame, height=5, width=40, font=self.fonts["body"], bd=1, relief="solid", bg=self.colors["card_bg"], fg=self.colors["text_primary"])
        self.note_text_widget.pack(pady=(5, 0))
        
        # Char Count Label
        self.char_count_label = ttk.Label(note_frame, text=f"0/{self.note_char_limit}", style="Small.TLabel")
        self.char_count_label.pack(anchor="e", padx=100)
        
        # Bind key release to update counter and limit text
        self.note_text_widget.bind('<KeyRelease>', self.check_note_limit)
        
        if current_note: 
            self.note_text_widget.insert("1.0", current_note)
            self.check_note_limit() # Update count immediately

        # --- Tags/Checkbox Section ---
        if tag_kpis:
            tag_section_frame = ttk.Frame(footer_frame, style="Main.TFrame")
            tag_section_frame.pack(fill='x', pady=(10, 5))

            ttk.Label(tag_section_frame, text="Daily Activities:", style="BgBody.TLabel").pack(anchor="center", pady=(10, 5))
            
            tag_list_container = ttk.Frame(tag_section_frame, style="Main.TFrame", padding=10)
            tag_list_container.pack(anchor="center") 

            for kpi_data in tag_kpis:
                name = kpi_data['name']
                val = current_scores.get(name, 0)
                
                var = tk.IntVar(value=int(val))
                self.check_vars[name] = var
                
                cb = ttk.Checkbutton(tag_list_container, text=name, variable=var, style="TCheckbutton")
                cb.pack(anchor='w', pady=2)

    def check_note_limit(self, event=None):
        """Enforces character limit on note input."""
        text = self.note_text_widget.get("1.0", "end-1c")
        current_len = len(text)
        
        if current_len > self.note_char_limit:
            # Truncate
            self.note_text_widget.delete(f"1.0 + {self.note_char_limit} chars", "end")
            text = self.note_text_widget.get("1.0", "end-1c")
            current_len = len(text)
            
        self.char_count_label.config(text=f"{current_len}/{self.note_char_limit}")

    # --- Tab 2: History (Line Graph) ---

    def build_history_tab(self):
        for widget in self.tab_history.winfo_children(): widget.destroy()

        header_frame = ttk.Frame(self.tab_history, style="Main.TFrame")
        header_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(header_frame, text="Wellbeing Trends", style="H1.TLabel").pack(side='left')

        graph_card = ttk.Frame(self.tab_history, style="Card.TFrame", padding=10)
        graph_card.pack(fill='both', expand=True, padx=10, pady=10)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor(self.colors["card_bg"])
        self.ax = self.figure.add_subplot(111)
        self.canvas_widget = FigureCanvasTkAgg(self.figure, master=graph_card)
        self.canvas_widget.get_tk_widget().pack(fill='both', expand=True)
        self.canvas_widget.mpl_connect("button_press_event", self.right_click_graph_handler)

    # --- Tab 3: Insights & Heatmap ---

    def build_insights_tab(self):
        for widget in self.tab_insights.winfo_children(): widget.destroy()

        container = ttk.Frame(self.tab_insights, style="Main.TFrame")
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_col = ttk.Frame(container, style="Main.TFrame")
        left_col.pack(side='left', fill='both', expand=True, padx=10)
        right_col = ttk.Frame(container, style="Main.TFrame")
        right_col.pack(side='right', fill='both', expand=True, padx=10)

        # -- Heatmap Section --
        ttk.Label(left_col, text="Mood Calendar (Average Daily Mood)", style="H2.TLabel", background=self.colors["bg"]).pack(anchor='w', pady=(0,10))
        
        map_card = ttk.Frame(left_col, style="Card.TFrame", padding=10)
        map_card.pack(fill='both', expand=True)
        
        self.fig_map = Figure(figsize=(5, 5), dpi=100)
        self.fig_map.patch.set_facecolor(self.colors["card_bg"])
        self.ax_map = self.fig_map.add_subplot(111)
        self.canvas_map = FigureCanvasTkAgg(self.fig_map, master=map_card)
        self.canvas_map.get_tk_widget().pack(fill='both', expand=True)
        self.canvas_map.mpl_connect("button_press_event", self.right_click_calendar)

        # -- Stats Section --
        ttk.Label(right_col, text="Quick Insights", style="H2.TLabel", background=self.colors["bg"]).pack(anchor='w', pady=(0,10))
        
        stats_card = ttk.Frame(right_col, style="Card.TFrame", padding=20)
        stats_card.pack(fill='both', expand=True)

        self.stats_text = tk.Text(stats_card, font=self.fonts["body"], bg=self.colors["bg"], fg=self.colors["text_primary"], bd=0, relief="flat", height=20)
        self.stats_text.pack(fill='both', expand=True)

    # --- Tab 4: Settings ---

    def build_settings_tab(self):
        for widget in self.tab_settings.winfo_children(): widget.destroy()

        content = ttk.Frame(self.tab_settings, style="Main.TFrame", padding=40)
        content.pack(fill='both', expand=True)

        ttk.Label(content, text="Settings", style="H1.TLabel").pack(anchor='w', pady=(0, 20))

        # Dark Mode
        dm_frame = ttk.Frame(content, style="Main.TFrame")
        dm_frame.pack(fill='x', pady=10)
        ttk.Label(dm_frame, text="Dark Mode", style="BgBody.TLabel").pack(side='left')
        btn_dm = ttk.Button(dm_frame, text="Toggle Theme", style="Secondary.TButton", command=self.toggle_theme)
        btn_dm.pack(side='right')

        # Export
        exp_frame = ttk.Frame(content, style="Main.TFrame")
        exp_frame.pack(fill='x', pady=10)
        ttk.Label(exp_frame, text="Export Data", style="BgBody.TLabel").pack(side='left')
        ttk.Button(exp_frame, text="Export PDF", style="Secondary.TButton", command=self.export_to_pdf).pack(side='right', padx=5)
        ttk.Button(exp_frame, text="Export CSV", style="Secondary.TButton", command=self.export_to_csv).pack(side='right', padx=5)

        # Security
        sec_frame = ttk.Frame(content, style="Main.TFrame")
        sec_frame.pack(fill='x', pady=10)
        ttk.Label(sec_frame, text="Security", style="BgBody.TLabel").pack(side='left')
        btn_txt = "Change Password" if self.current_user_password_hash else "Set Password"
        ttk.Button(sec_frame, text=btn_txt, style="Danger.TButton", command=self.set_password_dialog).pack(side='right')

    # --- Logic & Helpers ---

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.save_config()
        self.setup_colors()
        self.setup_styles()
        self.build_main_app()

    def set_password_dialog(self):
        pwd = simpledialog.askstring("Security", "Enter new password:", show="*")
        if pwd:
            self.current_user_password_hash = hashlib.sha256(pwd.encode()).hexdigest()
            self.save_config()
            messagebox.showinfo("Success", "Password updated.")

    def get_score_color(self, value):
        val = float(value)
        def hex_to_rgb(hex_col): return tuple(int(hex_col.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb): return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        red = hex_to_rgb(self.colors["danger"])
        blue = hex_to_rgb(self.colors["accent"])
        green = hex_to_rgb(self.colors["success"])
        
        if val <= 5:
            ratio = val / 5.0
            r = int(red[0] * (1 - ratio) + blue[0] * ratio)
            g, b = int(red[1] * (1 - ratio) + blue[1] * ratio), int(red[2] * (1 - ratio) + blue[2] * ratio)
        else:
            ratio = (val - 5) / 5.0
            r = int(blue[0] * (1 - ratio) + green[0] * ratio)
            g, b = int(blue[1] * (1 - ratio) + green[1] * ratio), int(blue[2] * (1 - ratio) + green[2] * ratio)
        return rgb_to_hex((r, g, b))

    def update_label(self, kpi, value):
        color = self.get_score_color(value)
        self.score_labels[kpi].config(text=f"{float(value):.1f}", foreground=color)

    def add_kpi_dialog(self):
        width, height = 400, 250
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Metric")
        dialog.configure(bg=self.colors["bg"])
        self.center_dialog(dialog, width, height)

        ttk.Label(dialog, text="Metric Name:", style="BgBody.TLabel").pack(pady=(10, 5))
        entry_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=entry_var).pack(pady=5, padx=30, fill='x')

        ttk.Label(dialog, text="Type:", style="BgBody.TLabel").pack(pady=(10, 5))
        type_var = tk.StringVar(value="slider")
        
        rb_frame = ttk.Frame(dialog, style="Main.TFrame")
        rb_frame.pack()
        
        s = ttk.Style()
        s.configure("TRadiobutton", background=self.colors["bg"], foreground=self.colors["text_primary"])
        
        ttk.Radiobutton(rb_frame, text="Score (0-10)", variable=type_var, value="slider", style="TRadiobutton").pack(side='left', padx=10)
        ttk.Radiobutton(rb_frame, text="Activity Tag (Yes/No)", variable=type_var, value="tag", style="TRadiobutton").pack(side='left', padx=10)

        def confirm():
            name = entry_var.get().strip()
            if name and not any(k['name'] == name for k in self.data['kpis']):
                self.data['kpis'].append({"name": name, "type": type_var.get()})
                self.save_data()
                self.build_input_tab()
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Invalid or duplicate name.")

        ttk.Button(dialog, text="Add", style="Accent.TButton", command=confirm).pack(pady=20)

    def remove_kpi_dialog(self):
        if not self.data['kpis']: return
        width, height = 350, 180
        dialog = tk.Toplevel(self.root)
        dialog.title("Remove")
        dialog.configure(bg=self.colors["bg"])
        self.center_dialog(dialog, width, height)

        ttk.Label(dialog, text="Select metric:", style="BgBody.TLabel").pack(pady=(20, 10))
        names = [k['name'] for k in self.data['kpis']]
        combo = ttk.Combobox(dialog, values=names, state="readonly")
        combo.pack(pady=5, padx=30, fill='x')
        combo.current(0)

        def confirm():
            sel = combo.get()
            if messagebox.askyesno("Confirm", f"Stop tracking '{sel}'?"):
                self.data['kpis'] = [k for k in self.data['kpis'] if k['name'] != sel]
                self.save_data()
                self.build_input_tab()
                dialog.destroy()

        ttk.Button(dialog, text="Remove", style="Danger.TButton", command=confirm).pack(pady=20)

    def center_dialog(self, dialog, width, height):
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def save_today(self):
        today = datetime.date.today().isoformat()
        new_scores = {}
        
        # Sliders
        for k, scale in self.sliders.items(): new_scores[k] = float(scale.get())
        # Checkboxes
        for k, var in self.check_vars.items(): new_scores[k] = float(var.get())

        note = self.note_text_widget.get("1.0", "end-1c").strip()
        # Enforce strict limit on save just in case
        if len(note) > self.note_char_limit:
            note = note[:self.note_char_limit]
        
        entry = self.get_today_entry()
        if entry:
            entry['scores'] = new_scores
            entry['note'] = note
        else:
            self.data['history'].append({"date": today, "scores": new_scores, "note": note})
        
        self.save_data()
        messagebox.showinfo("Saved", "Log saved successfully!")

    def on_tab_change(self, event):
        tab = event.widget.tab(event.widget.select(), "text").strip()
        if "History" in tab: self.refresh_graph()
        if "Insights" in tab: self.refresh_insights()

    # --- Charts & Insights ---

    def refresh_graph(self):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["card_bg"])
        self.figure.patch.set_facecolor(self.colors["card_bg"])
        if not self.data['history']: return

        dates = [e['date'] for e in self.data['history']]
        for kpi in self.data['kpis']:
            if kpi.get('type') == 'tag': continue 
            scores = [e['scores'].get(kpi['name'], None) for e in self.data['history']]
            self.ax.plot(dates, scores, marker='o', label=kpi['name'])

        self.ax.set_ylim(0, 10.5)
        self.ax.legend(frameon=False)
        self.ax.grid(True, linestyle=':', alpha=0.3)
        self.figure.autofmt_xdate()
        
        self.ax.tick_params(colors=self.colors["text_secondary"])
        self.ax.spines['bottom'].set_color(self.colors["border"])
        self.ax.spines['left'].set_color(self.colors["border"])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.canvas_widget.draw()

    def right_click_graph_handler(self, event):
        if event.button != 3 or event.inaxes != self.ax or not self.data['history']:
            return
        
        if event.xdata is not None:
            x_data_points = list(range(len(self.data['history'])))
            distances = [abs(event.xdata - x) for x in x_data_points]
            if not distances: return
                
            min_dist = min(distances)
            if min_dist < 0.5: 
                idx = x_data_points[distances.index(min_dist)]
                entry = self.data['history'][idx]
                
                note_content = entry.get('note', '').strip() or "No note recorded."
                messagebox.showinfo(f"Note for {entry['date']}", f"Daily Reflection:\n\n{note_content}")

    def right_click_calendar(self, event):
        if event.button != 3 or event.inaxes != self.ax_map or not self.data['history']:
            return
            
        if event.xdata is not None and event.ydata is not None:
            col = int(round(event.xdata))
            row = int(round(event.ydata))

            if 0 <= row < 5 and 0 <= col < 7:
                today = datetime.date.today()
                i = (4 - row) * 7 + (6 - col)
                d = today - datetime.timedelta(days=i)
                date_str = d.isoformat()
                
                entry = next((e for e in self.data['history'] if e['date'] == date_str), None)
                
                if entry:
                    avg_mood = self.get_daily_average_mood(entry)
                    mood_info = f"Avg Mood: {avg_mood:.1f}" if avg_mood >= 0 else "No score data"
                    note_content = entry.get('note', '').strip() or "No detailed note."
                    
                    messagebox.showinfo(f"Note for {date_str}", f"{mood_info}\n\nDaily Reflection:\n\n{note_content}")
                else:
                    messagebox.showinfo(f"Note for {date_str}", "No data recorded for this day.")


    def get_stats_report_text(self):
        """Generates the statistics text for display and PDF."""
        txt = "📊 STATISTICS REPORT\n" + "-"*30 + "\n\n"
        
        if not self.data['history']:
            txt += "No data available."
        else:
            slider_metrics = [k['name'] for k in self.data['kpis'] if k.get('type') == 'slider']
            
            # Averages
            txt += "AVERAGES:\n"
            for k in self.data['kpis']:
                name = k['name']
                vals = [e['scores'].get(name, 0) for e in self.data['history'] if name in e['scores']]
                if vals:
                    avg = sum(vals)/len(vals)
                    kind = " (Score)" if k.get('type') == 'slider' else " (Freq)"
                    fmt = f"{avg:.1f}/10" if k.get('type') == 'slider' else f"{avg*100:.0f}%"
                    txt += f"• {name}: {fmt}\n"
            
            # --- FULL CORRELATIONS ---
            txt += "\nCORRELATIONS (All Pairs):\n"
            if len(self.data['history']) > 2 and len(slider_metrics) >= 2:
                
                calculated_correlations = []
                
                # Iterate through every possible unique pair of slider metrics
                for m1, m2 in itertools.combinations(slider_metrics, 2):
                    v1 = [e['scores'].get(m1, 0) for e in self.data['history']]
                    v2 = [e['scores'].get(m2, 0) for e in self.data['history']]
                    
                    # Ensure variance exists (cannot correlate if all values are identical)
                    if np.var(v1) > 0 and np.var(v2) > 0:
                        corr = np.corrcoef(v1, v2)[0, 1]
                        calculated_correlations.append((m1, m2, corr))
                
                # Sort by strength of correlation (absolute value), highest first
                calculated_correlations.sort(key=lambda x: abs(x[2]), reverse=True)
                
                if calculated_correlations:
                    for m1, m2, corr in calculated_correlations:
                        txt += f"• {m1} vs {m2}: {corr:.2f}\n"
                else:
                    txt += "• Not enough variance data to calculate.\n"
            else:
                 txt += "• Need more data/metrics.\n"

            # Best Day
            txt += "\nBEST DAY:\n"
            best_date = None
            best_sum = -1
            for e in self.data['history']:
                s = sum([v for k,v in e['scores'].items() if k in slider_metrics])
                if s > best_sum:
                    best_sum = s
                    best_date = e['date']
            if best_date:
                txt += f"• {best_date} (Sum: {best_sum:.1f})\n"
        return txt

    def refresh_insights(self):
        # 1. Heatmap
        self.ax_map.clear()
        self.fig_map.patch.set_facecolor(self.colors["card_bg"])
        
        if not self.data['history']:
            self.ax_map.text(0.5, 0.5, "No data", ha='center')
        else:
            history_dict = {e['date']: self.get_daily_average_mood(e) for e in self.data['history']}
            grid = np.zeros((5, 7))
            dates_map = [["" for _ in range(7)] for _ in range(5)]
            today = datetime.date.today()
            
            for i in range(35): 
                d = today - datetime.timedelta(days=i)
                row, col = (4 - (i // 7)), (6 - (i % 7)) 
                val = history_dict.get(d.isoformat(), -1)
                grid[row, col] = val
                dates_map[row][col] = d.day

            cmap = plt.cm.RdYlGn
            masked_grid = np.ma.masked_where(grid < 0, grid)
            
            im = self.ax_map.imshow(masked_grid, cmap=cmap, vmin=0, vmax=10)
            
            for r in range(5):
                for c in range(7):
                    txt = dates_map[r][c]
                    if txt: self.ax_map.text(c, r, str(txt), ha='center', va='center', fontsize=8, color="#333")

            self.ax_map.set_xticks([])
            self.ax_map.set_yticks([])
            self.ax_map.set_title("Last 35 Days: Average Daily Mood", color=self.colors["text_primary"])
        
        self.canvas_map.draw()

        # 2. Stats Text
        txt = self.get_stats_report_text()
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", txt)

    # --- Exports ---

    def export_to_csv(self):
        if not self.data['history']: return
        
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not f: return
        
        try:
            with open(f, 'w', newline='') as csvfile:
                fieldnames = ['date', 'note'] + [k['name'] for k in self.data['kpis']]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for e in self.data['history']:
                    row = {'date': e['date'], 'note': e.get('note','').replace('\n', ' ')}
                    row.update(e['scores'])
                    writer.writerow(row)
            messagebox.showinfo("Success", "Exported to CSV.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_to_pdf(self):
        A4_LANDSCAPE = (11.69, 8.27) 
        
        if not self.data['history']: return
        try:
            with PdfPages("mood_report.pdf") as pdf:
                
                # Page 1: Line Graph
                fig_graph = plt.figure(figsize=A4_LANDSCAPE)
                dates = [e['date'] for e in self.data['history']]
                for k in self.data['kpis']:
                    if k.get('type')=='slider':
                        plt.plot(dates, [e['scores'].get(k['name'],0) for e in self.data['history']], marker='o', label=k['name'])
                plt.legend()
                plt.title("Wellbeing Trends")
                pdf.savefig(fig_graph)
                plt.close(fig_graph)

                # Page 2: Insights and Mood Calendar
                fig_page2 = plt.figure(figsize=A4_LANDSCAPE)
                fig_page2.patch.set_facecolor('white')

                # --- 2A. Mood Calendar ---
                ax_map = fig_page2.add_subplot(2, 1, 1) 
                
                slider_metrics = [k['name'] for k in self.data['kpis'] if k.get('type') == 'slider']
                if self.data['history'] and slider_metrics:
                    history_dict = {e['date']: self.get_daily_average_mood(e) for e in self.data['history']}
                    grid = np.zeros((5, 7))
                    dates_map = [["" for _ in range(7)] for _ in range(5)]
                    today = datetime.date.today()
                    
                    for i in range(35):
                        d = today - datetime.timedelta(days=i)
                        row, col = (4 - (i // 7)), (6 - (i % 7))
                        val = history_dict.get(d.isoformat(), -1)
                        grid[row, col] = val
                        dates_map[row][col] = d.day

                    cmap = plt.cm.RdYlGn
                    masked_grid = np.ma.masked_where(grid < 0, grid)
                    
                    ax_map.imshow(masked_grid, cmap=cmap, vmin=0, vmax=10)
                    for r in range(5):
                        for c in range(7):
                            txt = dates_map[r][c]
                            if txt: ax_map.text(c, r, str(txt), ha='center', va='center', fontsize=9, color="#333")

                    ax_map.set_xticks([])
                    ax_map.set_yticks([])
                    ax_map.set_title("Last 35 Days: Average Daily Mood Calendar", fontsize=14)
                else:
                    ax_map.text(0.5, 0.5, "Insufficient data for calendar.", ha='center')
                    ax_map.axis('off')

                # --- 2B. Insights Text ---
                ax_text = fig_page2.add_subplot(2, 1, 2)
                ax_text.axis('off')
                txt = self.get_stats_report_text()
                ax_text.text(0.05, 0.95, txt, transform=ax_text.transAxes, size=10, ha="left", va="top", wrap=True)
                
                fig_page2.tight_layout()
                pdf.savefig(fig_page2)
                plt.close(fig_page2)

                # Page 3: Raw Data Table
                fig_t, ax = plt.subplots(figsize=A4_LANDSCAPE); ax.axis('off')
                
                cols = ["Date", "Note"] + [k['name'] for k in self.data['kpis']] 
                rows = []
                for e in self.data['history']:
                    note_text = e.get('note', '').replace('\n', ' ')
                    # Double check limit here for PDF safety
                    if len(note_text) > self.note_char_limit:
                        note_text = note_text[:self.note_char_limit] + "..."
                        
                    r = [e['date'], note_text]
                    for k in self.data['kpis']:
                        val = e['scores'].get(k['name'], "-")
                        if k.get('type') == 'tag': val = "Yes" if val == 1.0 else "No"
                        r.append(str(val))
                    rows.append(r)
                
                table = ax.table(cellText=rows, colLabels=cols, loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(8)

                column_widths_prop = [0.15] # Date
                column_widths_prop.append(0.35) # Note
                
                num_cols = len(cols)
                num_rows = len(rows) + 1
                
                remaining_width = 1.0 - sum(column_widths_prop)
                remaining_cols = num_cols - len(column_widths_prop)
                width_per_other_col = remaining_width / remaining_cols if remaining_cols > 0 else 0
                column_widths_prop.extend([width_per_other_col] * remaining_cols)
                
                if num_cols > 0:
                    for (r_idx, c_idx), cell in table._cells.items():
                        if c_idx < len(column_widths_prop):
                            try:
                                cell.set_width(column_widths_prop[c_idx])
                            except Exception:
                                pass
                
                for i in range(num_rows):
                    cell_key = (i, 1)
                    if cell_key in table._cells:
                        cell = table._cells[cell_key]
                        try:
                            txt_obj = cell.get_text()
                            txt_obj.set_wrap(True)
                            txt_obj.set_ha('left')
                        except Exception:
                            pass
                    
                ax.set_title("Raw Data Log")
                fig_t.tight_layout()
                pdf.savefig(fig_t)
                plt.close(fig_t)
            
            messagebox.showinfo("Success", "Saved mood_report.pdf")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = MoodTrackerApp(root)
    root.mainloop()