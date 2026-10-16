import tkinter as tk
from tkinter import filedialog, messagebox
import pygame.mixer
import os
import random
import time
import threading
import queue
from mutagen import File
import io
import sys

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Music Player")
        self.root.resizable(False, False)

        # CHANGED: Increased buffer from 2048 to 4096 to prevent stuttering/glitching
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.mixer.init()

        self.theme = {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "btn_bg": "#1e1e1e",
            "slider_trough": "#444444",
            "active_bg": "#555555",
            "font_main": ("Helvetica", 12),
            "font_small": ("Helvetica", 10),
            "font_btn": ("Arial", 18),
        }
        self.root.config(bg=self.theme["bg"])

        self.playlist = []
        self.current_track_index = -1
        self.track_history = []
        self.state = {
            "is_playing": False, "is_paused": False, "is_dragging_slider": False,
            "last_play_time": 0, "paused_time": 0, "song_length": 0, "is_shuffle_mode": False,
        }
        
        # Queues for thread communication
        self.command_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        
        threading.Thread(target=self._playback_worker, daemon=True).start()

        self._setup_ui()
        self.root.bind("<space>", self._on_space_key)
        self.root.bind("<Left>", self._on_track_key)
        self.root.bind("<Right>", self._on_track_key)
        self.root.bind("<Up>", self._on_volume_key)
        self.root.bind("<Down>", self._on_volume_key)
        self.root.bind("<plus>", self._on_volume_key)
        self.root.bind("<minus>", self._on_volume_key)
        
        self._check_external_launch()
        
        self.root.after(250, self._update_ui_loop)

    def _setup_ui(self):
        self.track_label = self._create_widget(tk.Label, text="No track loaded", wraplength=380, font=self.theme["font_main"])
        self.track_label.pack(pady=15)

        progress_frame = self._create_widget(tk.Frame)
        progress_frame.pack(pady=5, fill=tk.X, padx=25)
        self.time_label = self._create_widget(tk.Label, progress_frame, text="--:-- / --:--", font=self.theme["font_small"])
        self.time_label.pack()
        self.progress_slider = self._create_widget(
            tk.Scale, progress_frame, from_=0, to=100, orient=tk.HORIZONTAL, showvalue=0,
            troughcolor=self.theme["slider_trough"], resolution=0.1, command=self._on_slider_move
        )
        self.progress_slider.bind("<ButtonPress-1>", lambda e: self.state.update({"is_dragging_slider": True}))
        self.progress_slider.bind("<ButtonRelease-1>", self._on_slider_release)
        self.progress_slider.pack(fill=tk.X, expand=True)

        controls_frame = self._create_widget(tk.Frame)
        controls_frame.pack(pady=20)
        buttons = [
            ("⏮", self.prev_track), ("▶", self.play_music), ("⏸", self.pause_music),
            ("⏹", self.stop_music), ("⏭", self.next_track), ("🎲", self.toggle_shuffle_mode)
        ]
        self.control_buttons = {}
        for i, (text, cmd) in enumerate(buttons):
            btn = self._create_widget(tk.Button, controls_frame, text=text, font=self.theme["font_btn"], command=cmd, borderwidth=0, bg=self.theme["btn_bg"], activebackground=self.theme["active_bg"])
            btn.grid(row=0, column=i, padx=10)
            self.control_buttons[text] = btn

        self.volume_slider = self._create_widget(
            tk.Scale, from_=1, to=0, orient=tk.VERTICAL, length=50, showvalue=0,
            troughcolor=self.theme["slider_trough"], resolution=0.01, command=self.set_volume
        )
        self.volume_slider.set(0.5)
        self.volume_slider.place(relx=0.98, rely=0.02, anchor='ne')
        self.volume_slider.bind("<MouseWheel>", self._on_mousewheel)
        self.volume_slider.bind("<Button-4>", self._on_mousewheel)
        self.volume_slider.bind("<Button-5>", self._on_mousewheel)

        load_frame = self._create_widget(tk.Frame)
        load_frame.pack(pady=20, fill=tk.X, padx=20)
        self._create_widget(tk.Button, load_frame, text="📂 Load Files", command=self.load_files, activebackground=self.theme["active_bg"]).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self._create_widget(tk.Button, load_frame, text="📁 Load Folder", command=self.load_folder, activebackground=self.theme["active_bg"]).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _create_widget(self, widget_class, master=None, **kwargs):
        if master is None: master = self.root
        style = {"bg": self.theme["bg"], "highlightbackground": self.theme["bg"]}
        if widget_class in (tk.Label, tk.Button, tk.Scale):
            style.update({"fg": self.theme["fg"], "activebackground": self.theme["active_bg"]})
        return widget_class(master, **{**style, **kwargs})

    def _playback_worker(self):
        while True:
            command, args = self.command_queue.get()
            try:
                if command == 'load_and_play':
                    pygame.mixer.music.stop() 
                    path = args['path']
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play(start=args.get('time', 0))
                    
                    length = self._get_song_length(path)
                    self.ui_queue.put({'type': 'meta_update', 'length': length, 'path': path})
                    
                elif command == 'play_from_memory':
                    mem_file = io.BytesIO(args['data'])
                    pygame.mixer.music.load(mem_file)
                    pygame.mixer.music.play(start=args.get('time', 0))
                elif command in ['pause', 'unpause', 'stop']:
                    getattr(pygame.mixer.music, command)()
            except Exception as e:
                print(f"Playback Error: {e}")
            finally:
                self.command_queue.task_done()

    def _update_ui_loop(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg['type'] == 'meta_update':
                    if self.playlist and self.playlist[self.current_track_index] == msg['path']:
                        self.state['song_length'] = msg['length']
                        self.progress_slider.config(to=self.state['song_length'])
                        self.time_label.config(text=f"--:-- / {self._format_time(self.state['song_length'])}")
        except queue.Empty:
            pass

        if self.state["is_playing"] and not self.state["is_paused"]:
            if not pygame.mixer.music.get_busy() and time.time() - self.state["last_play_time"] > 1.5:
                if self.state["is_shuffle_mode"]:
                    self.play_random_track()
                else:
                    self.next_track()
            elif not self.state["is_dragging_slider"]:
                elapsed = time.time() - self.state["last_play_time"]
                max_len = self.state['song_length'] if self.state['song_length'] > 0 else 100
                if 0 <= elapsed <= (max_len + 2):
                    self.time_label.config(text=f"{self._format_time(elapsed)} / {self._format_time(self.state['song_length'])}")
                    self.progress_slider.set(elapsed)
        self.root.after(250, self._update_ui_loop)

    def _update_track_info(self, index):
        if not self.playlist or not 0 <= index < len(self.playlist):
            self.track_label.config(text="No track loaded")
            self.state.update({"song_length": 0})
            self.progress_slider.config(to=0)
            self.time_label.config(text="--:-- / --:--")
            return
        
        self.current_track_index = index
        track_path = self.playlist[self.current_track_index]
        self.track_label.config(text=os.path.basename(track_path))
        
        self.state.update({"song_length": 0}) 
        self.progress_slider.config(to=100)
        self.progress_slider.set(0)
        self.time_label.config(text="--:-- / --:--")

    def _load_and_play_track(self, index, seek_time=0):
        if not self.playlist: return
        if self.current_track_index != index:
            self.track_history.append(self.current_track_index)
            if len(self.track_history) > 100: self.track_history.pop(0)
        
        self._update_track_info(index)
        self.state.update({"is_playing": True, "is_paused": False, "last_play_time": time.time() - seek_time})
        self.command_queue.put(('load_and_play', {'path': self.playlist[index], 'time': seek_time}))

    def play_music(self):
        if not self.playlist:
            messagebox.showwarning("No Playlist", "Please load some music files first.")
            return
        if self.state['is_paused']:
            resume_time = self.state['paused_time']
            self.state.update({"is_paused": False, "last_play_time": time.time() - resume_time})
            self.command_queue.put(('load_and_play', {'path': self.playlist[self.current_track_index], 'time': resume_time}))
        elif not self.state['is_playing']:
            self._load_and_play_track(self.current_track_index if self.current_track_index != -1 else 0)

    def pause_music(self):
        if self.state['is_playing'] and not self.state['is_paused']:
            current_elapsed = time.time() - self.state['last_play_time']
            self.state.update({"is_paused": True, "paused_time": current_elapsed})
            self.command_queue.put(('pause', None))

    def stop_music(self):
        if self.state['is_playing']:
            self.command_queue.put(('stop', None))
            self.state.update({"is_playing": False, "is_paused": False})
            self.progress_slider.set(0)
            self.time_label.config(text="--:-- / --:--")

    def next_track(self):
        if not self.playlist: return
        if self.state["is_shuffle_mode"]: self.play_random_track()
        else: self._load_and_play_track((self.current_track_index + 1) % len(self.playlist))

    def prev_track(self):
        if not self.track_history: return
        self._load_and_play_track(self.track_history.pop())

    def _on_space_key(self, event):
        if self.state['is_playing'] and not self.state['is_paused']:
            self.pause_music()
        else:
            self.play_music()

    def _on_track_key(self, event):
        if event.keysym == 'Left': self.prev_track()
        elif event.keysym == 'Right': self.next_track()

    def _on_volume_key(self, event):
        current_volume = self.volume_slider.get()
        if event.keysym in ['Up', 'plus']: new_volume = min(1.0, current_volume + 0.05)
        elif event.keysym in ['Down', 'minus']: new_volume = max(0.0, current_volume - 0.05)
        else: return
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)

    def toggle_shuffle_mode(self):
        self.state["is_shuffle_mode"] = not self.state["is_shuffle_mode"]
        btn = self.control_buttons.get("🎲")
        if btn: btn.config(bg=self.theme["active_bg"] if self.state["is_shuffle_mode"] else self.theme["btn_bg"])

    def play_random_track(self):
        if len(self.playlist) < 2: return
        self._load_and_play_track(random.randint(0, len(self.playlist) - 1))

    def load_files(self):
        file_types = [("Audio Files", " ".join(f"*.{ext}" for ext in ["mp3", "ogg", "flac", "m4a", "aac", "opus", "wav", "wma"]))]
        self._handle_loaded_files(filedialog.askopenfilenames(filetypes=file_types))

    def load_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            supported_formats = (".mp3", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wav", ".wma")
            files = [os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(supported_formats)]
            self._handle_loaded_files(files, show_warning=True)

    def _handle_loaded_files(self, files, show_warning=False):
        if files:
            self.stop_music()
            self.playlist = sorted(list(files))
            self._load_and_play_track(0)
        elif show_warning:
            messagebox.showwarning("No Music", "No audio files found.")

    def _check_external_launch(self):
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.isfile(file_path):
                self._handle_loaded_files([file_path])

    def set_volume(self, val):
        pygame.mixer.music.set_volume(float(val))

    def _on_mousewheel(self, event):
        current_volume = self.volume_slider.get()
        delta = 0.05 if event.num == 4 or event.delta > 0 else -0.05
        new_volume = max(0.0, min(1.0, current_volume + delta))
        self.volume_slider.set(new_volume)

    def _on_slider_move(self, value_str):
        if self.state['is_dragging_slider']:
            elapsed = float(value_str)
            self.time_label.config(text=f"{self._format_time(elapsed)} / {self._format_time(self.state['song_length'])}")

    def _on_slider_release(self, event):
        if self.state['is_dragging_slider'] and self.state['is_playing']:
            self.state.update({"is_dragging_slider": False})
            self._load_and_play_track(self.current_track_index, seek_time=self.progress_slider.get())

    @staticmethod
    def _format_time(seconds):
        if seconds is None: return "--:--"
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _get_song_length(file_path):
        try: return File(file_path).info.length
        except Exception as e:
            print(f"Error getting length for {file_path}: {e}")
            return 0

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    try: root.iconbitmap('icon.ico')
    except tk.TclError: pass
    root.mainloop()