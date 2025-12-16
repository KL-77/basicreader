import feedparser
import datetime
import time
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIGURATION ---
FEED_URLS = [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://futurism.com/feed",
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/TheAtlantic",
    "https://rsshub.app/reuters/technology",
    "https://rsshub.app/reuters/world",
    "https://rss.slashdot.org/Slashdot/slashdot",
    "https://slate.com/feeds/news-and-politics.rss",
    "https://techxplore.com/rss-feed/",
    "https://www.theregister.co.uk/headlines.atom",
    "https://www.thedebrief.org/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.technologyreview.com/topnews.rss",
    "https://thenextweb.com/feed/",
    "https://www.theinformation.com/feed"
]
# We limit to 3 articles per feed to keep the build fast (approx 12 articles total)
ARTICLES_PER_FEED = 3
# ---------------------

def scrape_article_text(url):
    """
    Downloads the article content using a Python web request.
    This runs on GitHub's servers, which are more powerful than a Kindle browser.
    """
    try:
        # We pretend to be a real Chrome browser on Windows to avoid getting blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Check for errors (like 404 or 500)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # REMOVE JUNK: specific to news sites (removes ads, "read more" links, menus)
        for junk in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'aside']):
            junk.decompose()

        # EXTRACT TEXT: Look for paragraph tags
        paragraphs = soup.find_all('p')
        
        # Filter out short/empty paragraphs that are usually captions or bylines
        valid_paragraphs = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40]
        
        text_content = "\n\n".join(valid_paragraphs)
        
        if len(text_content) < 200:
            return "Could not extract main text automatically. Please use the 'Read Original' link."
            
        return text_content
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return "Content unavailable (Blocked by source). Please read on original site."

def fetch_and_parse():
    articles = []
    
    print("Fetching feeds...")
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            print(f"Processing Feed: {feed.feed.get('title', url)}")
            
            # Only process the top N articles
            for entry in feed.entries[:ARTICLES_PER_FEED]:
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if not published:
                    published = time.localtime()
                
                print(f"  - Downloading: {entry.title[:40]}...")
                full_text = scrape_article_text(entry.link)
                
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'date': published,
                    'source': feed.feed.get('title', 'Unknown'),
                    # Escape quotes so they don't break the HTML attribute
                    'content': full_text.replace('"', '&quot;').replace("'", "&#39;")
                })
        except Exception as e:
            print(f"Error parsing feed {url}: {e}")

    return articles

def generate_html(articles):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KL-77's Feed</title>
        <style>
            :root {{
                --bg: #ffffff;
                --text: #000000;
                --border: #000000;
                --modal-bg: #ffffff;
                --dim: #666666;
            }}
            
            body.dark-mode {{
                --bg: #000000;
                --text: #ffffff;
                --border: #ffffff;
                --modal-bg: #000000;
                --dim: #aaaaaa;
            }}

            body {{ 
                font-family: Georgia, serif; 
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 10px;
                font-size: 22px; /* Large text for Kindle */
                line-height: 1.5;
            }}

            header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 3px solid var(--text);
                padding-bottom: 15px;
                margin-bottom: 25px;
            }}
            
            h1 {{ margin: 0; font-size: 1.2em; }}

            button#theme-toggle {{
                background: transparent;
                color: var(--text);
                border: 2px solid var(--text);
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 4px;
                cursor: pointer;
            }}

            .card {{
                border: 2px solid var(--text);
                margin-bottom: 25px;
                padding: 15px;
                cursor: pointer;
                /* No rounded corners on cards for crisp e-ink rendering */
            }}
            
            .source {{ font-size: 0.7em; font-weight: bold; text-transform: uppercase; color: var(--dim); }}
            .title {{ font-size: 1.1em; font-weight: bold; margin: 8px 0; display:block; }}
            .meta {{ font-size: 0.7em; color: var(--dim); }}

            /* MODAL STYLING */
            #reader-modal {{
                display: none;
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background-color: var(--modal-bg);
                z-index: 1000;
                overflow-y: scroll;
            }}

            #modal-inner {{
                padding: 25px;
                max-width: 800px;
                margin: 0 auto;
                padding-top: 80px; /* Space for close button */
            }}

            #close-btn {{
                position: fixed;
                top: 15px; right: 15px;
                width: 60px; height: 60px;
                line-height: 55px;
                text-align: center;
                border: 3px solid var(--text);
                background: var(--bg);
                color: var(--text);
                font-size: 30px;
                font-weight: bold;
                border-radius: 8px; /* Rounded corners requested */
                cursor: pointer;
                z-index: 1001;
            }}

            #article-text {{ white-space: pre-wrap; font-size: 1.1em; }}
            
            a.original-link {{
                display: inline-block;
                margin-top: 30px;
                padding: 15px;
                border: 1px solid var(--text);
                color: var(--text);
                text-decoration: none;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>

        <header>
            <h1>KL-77's Feed</h1>
            <button id="theme-toggle">Light/Dark</button>
        </header>

        <div id="feed-list">
    """

    for index, article in enumerate(articles):
        date_str = time.strftime("%Y-%m-%d", article['date'])
        
        # We store the scraped text in a hidden div next to the card
        html_content += f"""
        <div class="card" onclick="openModal('content-{index}')">
            <div class="source">{article['source']}</div>
            <div class="title">{article['title']}</div>
            <div class="meta">{date_str}</div>
        </div>
        
        <div id="content-{index}" style="display:none;">
            <h2>{article['title']}</h2>
            <p><strong>{article['source']} | {date_str}</strong></p>
            <hr style="border: 1px solid var(--text);">
            <div id="article-text">{article['content']}</div>
            <a class="original-link" href="{article['link']}">Visit Original Website</a>
        </div>
        """

    html_content += """
        </div>

        <div id="reader-modal">
            <div id="close-btn" onclick="closeModal()">X</div>
            <div id="modal-inner"></div>
        </div>

        <script>
            // 1. RANDOMIZE ORDER
            const list = document.getElementById('feed-list');
            // We move pairs of elements (card + hidden div) so we need to be careful.
            // Simplified: We just randomize the visual cards and map clicks correctly.
            // Actually, simpler approach: Randomize the HTML string generation in Python? 
            // No, let's just randomize the children nodes safely.
            
            // Collect all cards
            const cards = Array.from(document.querySelectorAll('.card'));
            const container = document.getElementById('feed-list');
            
            // Shuffle them
            cards.sort(() => Math.random() - 0.5);
            
            // Re-append them (The hidden divs can stay where they are, we reference them by ID)
            cards.forEach(card => container.appendChild(card));

            // 2. DARK MODE
            const btn = document.getElementById('theme-toggle');
            btn.addEventListener('click', () => document.body.classList.toggle('dark-mode'));

            // 3. MODAL LOGIC
            const modal = document.getElementById('reader-modal');
            const modalInner = document.getElementById('modal-inner');

            function openModal(contentId) {
                const content = document.getElementById(contentId).innerHTML;
                modalInner.innerHTML = content;
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden'; // Stop background scrolling
            }

            function closeModal() {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Successfully generated index.html")

if __name__ == "__main__":
    data = fetch_and_parse()
    generate_html(data)

'''import feedparser
import datetime
import time

# --- CONFIGURATION ---
FEED_URLS = [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://futurism.com/feed",
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/TheAtlantic",
    "https://rsshub.app/reuters/technology",
    "https://rsshub.app/reuters/world",
    "https://rss.slashdot.org/Slashdot/slashdot",
    "https://slate.com/feeds/news-and-politics.rss",
    "https://techxplore.com/rss-feed/",
    "https://www.theregister.co.uk/headlines.atom",
    "https://www.thedebrief.org/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.technologyreview.com/topnews.rss",
    "https://thenextweb.com/feed/",
    "https://www.theinformation.com/feed"
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
'''
