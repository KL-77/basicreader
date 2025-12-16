import feedparser
import datetime
import time

# --- CONFIGURATION ---
FEED_URLS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://news.ycombinator.com/rss",
]
# ---------------------

def fetch_and_parse():
    articles = []
    
    print("Fetching feeds...")
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            print(f"Loaded: {feed.feed.get('title', url)}")
            
            for entry in feed.entries:
                # Standardize date parsing
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if not published:
                    published = time.localtime() # Fallback to now if no date
                
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'date': published,
                    'source': feed.feed.get('title', 'Unknown Source'),
                    'summary': entry.get('summary', '')[:200] + '...' # Truncate summary
                })
        except Exception as e:
            print(f"Error parsing {url}: {e}")

    # Sort articles by date (newest first)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles

def generate_html(articles):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My RSS Aggregator</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f0f2f5; }}
            h1 {{ text-align: center; color: #333; }}
            .update-time {{ text-align: center; color: #666; font-size: 0.9em; margin-bottom: 30px; }}
            .card {{ background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-2px); }}
            .source {{ color: #e74c3c; font-weight: bold; font-size: 0.8em; text-transform: uppercase; }}
            .title {{ display: block; font-size: 1.2em; font-weight: bold; margin: 8px 0; color: #2c3e50; text-decoration: none; }}
            .title:hover {{ color: #3498db; }}
            .meta {{ color: #95a5a6; font-size: 0.85em; }}
        </style>
    </head>
    <body>
        <h1>My Personal Feed</h1>
        <div class="update-time">Last updated: {timestamp}</div>
        <div id="feed-list">
    """

    for article in articles:
        # Format date for display
        date_str = time.strftime("%Y-%m-%d %H:%M", article['date'])
        
        html_content += f"""
        <div class="card">
            <span class="source">{article['source']}</span>
            <a href="{article['link']}" class="title" target="_blank">{article['title']}</a>
            <div class="meta">{date_str}</div>
        </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Successfully generated index.html")

if __name__ == "__main__":
    data = fetch_and_parse()
    generate_html(data)
