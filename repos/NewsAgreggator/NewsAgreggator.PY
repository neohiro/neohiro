import tkinter as tk
from tkinter import scrolledtext, messagebox, font as tkfont
import threading
import feedparser
import webbrowser
from datetime import datetime
from dateutil import parser
import time
import html
import re
import os

# Expanded list of international RSS feed URLs.
RSS_FEEDS = [
    # Americas
    "https://feeds.bbci.co.uk/news/world/rss.xml", # BBC World
    "https://feeds.nbcnews.com/nbcnews/public/news", # NBC News
    "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml", # New York Times
    "https://feeds.washingtonpost.com/rss/world", # Washington Post
    "https://globalnews.ca/world/feed/", # Global News (Canada)
    "http://www.buenosairesherald.com/rss", # Buenos Aires Herald (Argentina)
    
    # Europe
    "http://www.theguardian.com/world/rss", # The Guardian (UK)
    "https://www.france24.com/en/rss", # France 24
    "https://www.spiegel.de/international/index.rss", # Der Spiegel (Germany)
    "https://www.euronews.com/rss?format=mrss&level=theme&name=news", # Euronews
    "https://www.independent.co.uk/news/world/rss", # The Independent (UK)

    # Asia
    "https://www.aljazeera.com/xml/rss/all.xml", # Al Jazeera (Qatar)
    "https://www.japantimes.co.jp/feed/top-stories/", # The Japan Times
    "https://www.scmp.com/rss/91/feed", # South China Morning Post (Hong Kong)
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", # Times of India
    
    # Africa & Middle East
    "https://mg.co.za/feed/", # Mail & Guardian (South Africa)
    "https://www.dailynewsegypt.com/feed/", # Daily News Egypt
    
    # Oceania
    "https://www.smh.com.au/rss/world.xml" # Sydney Morning Herald (Australia)
]

class NewsAggregatorApp(tk.Tk):
    """
    Main application window for the news aggregator GUI using Tkinter.
    """
    def __init__(self):
        super().__init__()
        self.title("Global News Aggregator")
        self.geometry("1200x800")
        
        # Set application icon
        try:
            # The icon file 'icon.ico' must be in the same directory as the script
            if os.path.exists('icon.ico'):
                self.iconbitmap('icon.ico')
        except tk.TclError:
            print("Icon 'icon.ico' not found. Skipping icon setting.")
            
        self.all_articles = []
        self.is_search_active = False

        # Configure dark theme colors
        self.bg_color = "#2c2f33"
        self.fg_color = "#ffffff"
        self.header_color = "#7289da"
        self.frame_color = "#40444b"
        self.search_btn_active_color = "#99aab5"
        self.config(bg=self.bg_color)
        
        self.create_widgets()
        self.fetch_articles()

    def create_widgets(self):
        """Creates all the GUI elements for the application."""
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_font = tkfont.Font(family="Helvetica", size=20, weight="bold")
        title_label = tk.Label(main_frame, text="Global News Headlines", font=title_font, fg=self.header_color, bg=self.bg_color)
        title_label.pack(pady=(0, 10))

        search_frame = tk.Frame(main_frame, bg=self.bg_color)
        search_frame.pack(fill="x", pady=10)

        self.search_entry = tk.Entry(search_frame, width=50, bg=self.frame_color, fg=self.fg_color, insertbackground=self.fg_color, relief="flat", font=("Helvetica", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)
        self.search_entry.bind("<Return>", lambda event: self.perform_search())
        self.search_entry.bind("<KeyRelease>", self.on_search_entry_change)

        self.search_button = tk.Button(search_frame, text="Search", bg=self.header_color, fg=self.fg_color, relief="flat", font=("Helvetica", 12), command=self.perform_search)
        self.search_button.pack(side="left", padx=(0, 10), ipady=5)

        self.refresh_button = tk.Button(search_frame, text="Refresh", bg=self.header_color, fg=self.fg_color, relief="flat", font=("Helvetica", 12), command=self.fetch_articles)
        self.refresh_button.pack(side="left", ipady=5)

        self.articles_display = scrolledtext.ScrolledText(main_frame, bg=self.frame_color, fg=self.fg_color, relief="flat", font=("Helvetica", 14), wrap=tk.WORD, insertbackground=self.fg_color, padx=10)
        self.articles_display.pack(fill="both", expand=True, pady=10)
        
        self.status_label = tk.Label(main_frame, text="Ready", font=("Helvetica", 10), fg=self.fg_color, bg=self.bg_color, anchor='w')
        self.status_label.pack(fill="x")

        # Tags for styling and linking
        self.articles_display.tag_config("link", foreground="#8da6ff", underline=True)
        self.articles_display.tag_bind("link", "<Enter>", lambda e: self.articles_display.config(cursor="hand2"))
        self.articles_display.tag_bind("link", "<Leave>", lambda e: self.articles_display.config(cursor=""))
        self.articles_display.tag_config("source", foreground="#99aab5", font=("Helvetica", 12, "italic"))
        self.articles_display.tag_config("summary", foreground="#dcddde", font=("Helvetica", 14))

    def update_status(self, message):
        """Updates the status bar label."""
        self.status_label.config(text=message)
        self.update_idletasks()

    def fetch_articles(self):
        """Starts a new thread to fetch articles to keep the GUI responsive."""
        self.update_status("Fetching news, please wait...")
        self.articles_display.config(state="normal")
        self.articles_display.delete("1.0", tk.END)
        self.articles_display.insert(tk.END, "Fetching news, please wait...")
        self.articles_display.config(state="disabled")
        
        # Clear search state on refresh
        self.search_entry.delete(0, tk.END)
        self.is_search_active = False
        self.search_button.config(text="Search", bg=self.header_color)

        fetch_thread = threading.Thread(target=self.fetch_articles_in_thread)
        fetch_thread.daemon = True
        fetch_thread.start()

    def fetch_articles_in_thread(self):
        """Worker function to fetch all articles from RSS feeds."""
        temp_articles = []
        for url in RSS_FEEDS:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get('title', 'Unknown Source')
                for entry in feed.entries:
                    # Use dateutil.parser for robust, timezone-aware date parsing
                    date_obj = None
                    if 'published' in entry:
                        try:
                            date_obj = parser.parse(entry.published)
                        except parser.ParserError:
                            # Fallback for unparsable dates
                            date_obj = datetime.fromtimestamp(time.mktime(entry.published_parsed)) if hasattr(entry, 'published_parsed') else None
                    
                    # Clean up summary from HTML tags
                    summary_html = entry.get('summary', 'No summary available.')
                    # First, unescape HTML entities like &amp;, &lt;, etc.
                    summary_text_unescaped = html.unescape(summary_html)
                    # Then, remove all HTML tags using a regular expression
                    summary_text_clean = re.sub(r'<[^>]+>', '', summary_text_unescaped).strip()

                    temp_articles.append({
                        'title': entry.get('title', 'No Title'),
                        'summary': summary_text_clean if summary_text_clean else 'No summary available.',
                        'source': source_name,
                        'date_obj': date_obj,
                        'link': entry.get('link', '#'),
                    })
            except Exception as e:
                print(f"Error fetching feed from {url}: {e}")

        self.all_articles = temp_articles
        # Safely call the display function from the main thread
        self.after(0, self.display_articles, self.all_articles)
    
    def display_articles(self, articles):
        """Displays articles in the ScrolledText widget and binds unique link tags."""
        self.articles_display.config(state="normal")
        self.articles_display.delete("1.0", tk.END)

        # Sort articles by the timezone-aware datetime object, newest first
        # Articles without a valid date are placed at the end.
        articles.sort(key=lambda x: x.get('date_obj') or datetime.min.replace(tzinfo=None), reverse=True)
        
        if not articles:
            self.articles_display.insert(tk.END, "No articles found.")
        else:
            for i, article in enumerate(articles):
                link_tag = f"link_{i}"
                
                self.articles_display.insert(tk.END, f"{article.get('title')}\n", (link_tag, "link"))
                self.articles_display.tag_bind(link_tag, "<Button-1>", lambda e, url=article.get('link'): self.open_link(url))
                
                date_str = article['date_obj'].strftime('%Y-%m-%d %H:%M %Z') if article['date_obj'] else 'No Date'
                self.articles_display.insert(tk.END, f"  Source: {article.get('source')} - {date_str}\n", "source")
                self.articles_display.insert(tk.END, f"  Summary: {article.get('summary')}\n\n", "summary")
        
        self.articles_display.config(state="disabled")
        self.update_status(f"Displaying {len(articles)} articles.")

    def on_search_entry_change(self, event=None):
        """Resets the search button to 'Search' when the user types a new query."""
        button_text = self.search_button.cget("text")
        if button_text == "Clear":
            self.search_button.config(text="Search", bg=self.header_color)
            self.is_search_active = False
        
    def perform_search(self):
        """Performs a search or clears the search based on the button's state."""
        button_text = self.search_button.cget("text")

        if button_text == "Search":
            query = self.search_entry.get().strip().lower()
            if query:
                filtered_articles = [
                    article for article in self.all_articles
                    if query in article.get('title', '').lower() or
                       query in article.get('summary', '').lower()
                ]
                self.display_articles(filtered_articles)
                self.is_search_active = True
                self.search_button.config(text="Clear", bg=self.search_btn_active_color)
            else:
                # If search is clicked with no query, just ensure everything is reset
                self.display_articles(self.all_articles)
                self.is_search_active = False
        
        elif button_text == "Clear":
            self.search_entry.delete(0, tk.END)
            self.display_articles(self.all_articles)
            self.is_search_active = False
            self.search_button.config(text="Search", bg=self.header_color)
        
    def open_link(self, url):
        """Opens the provided URL in the user's default web browser."""
        if url and url != '#':
            try:
                webbrowser.open_new(url)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open link: {e}")
        else:
            messagebox.showinfo("No Link", "No link available for this article.")

if __name__ == "__main__":
    try:
        # You might need to install dateutil: pip install python-dateutil
        app = NewsAggregatorApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"An unexpected error occurred: {e}")
