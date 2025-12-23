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
    "https://www.theinformation.com/feed",
    "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen",
    "https://news.google.com/rss/search?q=site%3Athedebrief.org&hl=en-US&gl=US&ceid=US%3Aen",
    "https://news.google.com/rss/search?q=site%3Atheinformation.com&hl=en-US&gl=US&ceid=US%3Aen"
]
# Limit articles to keep things fast
ARTICLES_PER_FEED = 6
# ---------------------

def scrape_article_text(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove junk
        for junk in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'aside']):
            junk.decompose()

        # Extract text
        paragraphs = soup.find_all('p')
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
                font-size: 22px;
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
                overflow-y: scroll; /* Allow scrolling */
                scroll-behavior: auto; /* Instant scrolling for e-ink */
            }}

            #modal-inner {{
                padding: 25px;
                max-width: 800px;
                margin: 0 auto;
                padding-top: 80px; 
                padding-bottom: 150px; /* Huge padding so text clears the buttons */
            }}

            /* Controls (Close + Scroll) */
            .control-btn {{
                position: fixed;
                background: var(--bg);
                color: var(--text);
                border: 3px solid var(--text);
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                z-index: 1001;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            #close-btn {{
                top: 15px; right: 15px;
                width: 60px; height: 60px;
                font-size: 30px;
                line-height: 55px;
            }}

            /* Scroll Buttons */
            #scroll-controls {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
                z-index: 1002;
            }}

            .scroll-btn {{
                width: 60px;
                height: 60px;
                font-size: 24px;
                background: var(--bg);
                color: var(--text);
                border: 3px solid var(--text);
                border-radius: 8px;
                cursor: pointer;
            }}

            #article-text {{ white-space: pre-wrap; font-size: 1.1em; }}
            
            a.original-link {{
                display: inline-block;
                margin-bottom: 30px; /* Space before text starts */
                padding: 10px;
                border: 1px solid var(--text);
                color: var(--text);
                text-decoration: none;
                font-weight: bold;
                font-size: 0.8em;
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
        
        html_content += f"""
        <div class="card" onclick="openModal('content-{index}')">
            <div class="source">{article['source']}</div>
            <div class="title">{article['title']}</div>
            <div class="meta">{date_str}</div>
        </div>
        
        <div id="content-{index}" style="display:none;">
            <h2>{article['title']}</h2>
            <p><strong>{article['source']} | {date_str}</strong></p>
            <a class="original-link" href="{article['link']}">Visit Original Website</a>
            <hr style="border: 1px solid var(--text);">
            <div id="article-text">{article['content']}</div>
        </div>
        """

    html_content += """
        </div>

        <div id="reader-modal">
            <div id="close-btn" class="control-btn" onclick="closeModal()">X</div>
            
            <div id="scroll-controls">
                <button class="scroll-btn" onclick="scrollPage(-1)">&#9650;</button> <button class="scroll-btn" onclick="scrollPage(1)">&#9660;</button>  </div>

            <div id="modal-inner"></div>
        </div>

        <script>
            // 1. RANDOMIZE ORDER
            const list = document.getElementById('feed-list');
            const cards = Array.from(document.querySelectorAll('.card'));
            cards.sort(() => Math.random() - 0.5);
            cards.forEach(card => list.appendChild(card));

            // 2. DARK MODE
            const btn = document.getElementById('theme-toggle');
            btn.addEventListener('click', () => document.body.classList.toggle('dark-mode'));

            // 3. MODAL & SCROLL LOGIC
            const modal = document.getElementById('reader-modal');
            const modalInner = document.getElementById('modal-inner');

            function openModal(contentId) {
                const content = document.getElementById(contentId).innerHTML;
                modalInner.innerHTML = content;
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden'; 
            }

            function closeModal() {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }

            function scrollPage(direction) {
                // Scroll by 80% of the screen height to keep context
                const scrollAmount = window.innerHeight * 0.8;
                modal.scrollBy(0, direction * scrollAmount);
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
