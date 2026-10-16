# To run this script, you first need to install the playsound3 library:
# pip uninstall playsound
# pip install playsound3

# You also need to place your sound and icon files in the same directory as this script.
# The sound files should be named 'weather.mp3', 'time.mp3', 'news.mp3', and 'traffic.mp3'.
# The icon file should be named 'icon.ico'.

import tkinter as tk
from playsound3 import playsound
import threading
import os
import sys

# PyInstaller-specific function to handle resource paths
def resource_path(relative_path):
    """
    Get the absolute path to a resource file, handling PyInstaller's temporary
    directory. This is crucial for packaging the app into an executable.
    """
    try:
        # PyInstaller creates a temporary folder and stores the files there.
        base_path = sys._MEIPASS
    except Exception:
        # If not running as a frozen executable, use the current directory.
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Define a function to play a sound in a separate thread.
# This prevents the GUI from freezing while the sound plays.
def play_sound_async(file_path):
    """
    Plays a sound file asynchronously to avoid freezing the GUI.
    """
    thread = threading.Thread(target=playsound, args=(resource_path(file_path),))
    thread.daemon = True # Allows the thread to exit with the main program
    thread.start()

# --- Functions for each button's sound ---
def play_weather_sound():
    """
    Plays the weather sound.
    """
    try:
        play_sound_async('weather.mp3')
    except Exception as e:
        print(f"Error playing weather.mp3: {e}")

def play_time_sound():
    """
    Plays the time sound.
    """
    try:
        play_sound_async('time.mp3')
    except Exception as e:
        print(f"Error playing time.mp3: {e}")

def play_news_sound():
    """
    Plays the news sound.
    """
    try:
        play_sound_async('news.mp3')
    except Exception as e:
        print(f"Error playing news.mp3: {e}")

def play_traffic_sound():
    """
    Plays the traffic sound.
    """
    try:
        play_sound_async('traffic.mp3')
    except Exception as e:
        print(f"Error playing traffic.mp3: {e}")

# --- Set up the main application window ---
root = tk.Tk()
root.title("Google Command - FrenzyPenguin Media")
# The window will now size itself to fit its contents automatically.
root.configure(bg="#f0f0f0") # Light gray background

# Set the window icon using the PyInstaller-friendly function
root.iconbitmap(resource_path('icon.ico'))

# Use a Frame to contain the buttons for better layout control
main_frame = tk.Frame(root, bg="#f0f0f0")
main_frame.pack(padx=20, pady=20)

# --- Create and configure the buttons ---

# Common button style
button_style = {
    'font': ('Arial', 14, 'bold'),
    'bg': '#4CAF50', # Green background
    'fg': 'white',   # White text
    'activebackground': '#45a049',
    'activeforeground': 'white',
    'relief': 'raised',
    'bd': 5,
    'padx': 20,
    'pady': 10
}

# Weather Button
weather_button = tk.Button(main_frame, text="Weather", command=play_weather_sound, **button_style)
weather_button.pack(pady=10, fill=tk.X)

# Time Button
time_button = tk.Button(main_frame, text="Time", command=play_time_sound, **button_style)
time_button.pack(pady=10, fill=tk.X)

# News Button
news_button = tk.Button(main_frame, text="News", command=play_news_sound, **button_style)
news_button.pack(pady=10, fill=tk.X)

# Traffic Button
traffic_button = tk.Button(main_frame, text="Traffic", command=play_traffic_sound, **button_style)
traffic_button.pack(pady=10, fill=tk.X)

# --- Start the GUI event loop ---
root.mainloop()
