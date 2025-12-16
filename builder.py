import feedparser
import datetime
import time
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

# ---------------------

def fetch_and_parse():
    articles = []
    
    print("Fetching feeds...")
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            print(f"Loaded: {feed.feed.get('title', url)}")
            
            for entry in feed.entries[:10]: # Increased limit since we aren't scraping
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if not published:
                    published = time.localtime()
                
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'date': published,
                    'source': feed.feed.get('title', 'Unknown Source'),
                    # We don't scrape content here anymore!
                })
        except Exception as e:
            print(f"Error parsing {url}: {e}")

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
            }}
            
            body.dark-mode {{
                --bg: #000000;
                --text: #ffffff;
                --border: #ffffff;
                --modal-bg: #000000;
            }}

            body {{ 
                font-family: Georgia, serif; 
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 10px;
                font-size: 20px;
                line-height: 1.5;
            }}

            header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid var(--text);
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}

            button#theme-toggle {{
                background: transparent;
                color: var(--text);
                border: 2px solid var(--text);
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}

            .card {{
                border: 2px solid var(--text);
                margin-bottom: 20px;
                padding: 15px;
                cursor: pointer;
            }}
            
            .source {{ font-size: 0.7em; font-weight: bold; text-transform: uppercase; }}
            .title {{ font-size: 1.2em; font-weight: bold; margin: 5px 0; }}
            .meta {{ font-size: 0.7em; opacity: 0.8; }}

            /* MODAL */
            #reader-modal {{
                display: none;
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background-color: var(--modal-bg);
                z-index: 999;
                overflow-y: scroll;
            }}

            #modal-inner {{
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                padding-top: 60px;
            }}

            #close-btn {{
                position: fixed;
                top: 10px; right: 10px;
                width: 50px; height: 50px;
                line-height: 45px;
                text-align: center;
                border: 2px solid var(--text);
                background: var(--bg);
                font-size: 24px;
                font-weight: bold;
                cursor: pointer;
                z-index: 1000;
            }}

            #article-content {{ font-size: 1.1em; }}
            .loading {{ text-align: center; margin-top: 50px; font-style: italic; }}
        </style>
    </head>
    <body>
        <header>
            <h1>KL-77's Feed</h1>
            <button id="theme-toggle">Light/Dark</button>
        </header>

        <div id="feed-list">
    """

    for article in articles:
        date_str = time.strftime("%Y-%m-%d", article['date'])
        # We pass the URL to the onclick function
        html_content += f"""
        <div class="card" onclick="openArticle('{article['link']}', '{article['title'].replace("'", "")}')">
            <div class="source">{article['source']}</div>
            <div class="title">{article['title']}</div>
            <div class="meta">{date_str}</div>
        </div>
        """

    html_content += """
        </div>

        <div id="reader-modal">
            <div id="close-btn" onclick="closeModal()">X</div>
            <div id="modal-inner">
                <h2 id="modal-title"></h2>
                <div id="article-content"></div>
                <br>
                <a id="original-link" href="#" target="_blank">Read Original</a>
            </div>
        </div>

        <script>
            // RANDOMIZE LIST
            const list = document.getElementById('feed-list');
            for (let i = list.children.length; i >= 0; i--) {
                list.appendChild(list.children[Math.random() * i | 0]);
            }

            // DARK MODE
            const btn = document.getElementById('theme-toggle');
            btn.addEventListener('click', () => document.body.classList.toggle('dark-mode'));

            // READER LOGIC
            const modal = document.getElementById('reader-modal');
            const contentDiv = document.getElementById('article-content');
            const titleDiv = document.getElementById('modal-title');
            const linkTag = document.getElementById('original-link');

            async function openArticle(url, title) {
                modal.style.display = 'block';
                titleDiv.innerText = title;
                linkTag.href = url;
                contentDiv.innerHTML = '<div class="loading">Fetching article text...<br>(This may take a few seconds)</div>';
                
                try {
                    // Use AllOrigins Proxy to bypass CORS
                    const proxyUrl = 'https://api.allorigins.win/get?url=' + encodeURIComponent(url);
                    const response = await fetch(proxyUrl);
                    const data = await response.json();
                    
                    if (data.contents) {
                        // Parse the HTML string to find text
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(data.contents, 'text/html');
                        
                        // Try to find the main text container (heuristic)
                        const paragraphs = doc.querySelectorAll('p');
                        let textBlock = '';
                        
                        // Simple filter: only keep paragraphs with significant text
                        paragraphs.forEach(p => {
                            if (p.innerText.length > 60) {
                                textBlock += '<p>' + p.innerText + '</p>';
                            }
                        });

                        if (textBlock.length < 50) textBlock = "<p>Could not extract text. Please use the 'Read Original' link.</p>";
                        
                        contentDiv.innerHTML = textBlock;
                    } else {
                        throw new Error('No content');
                    }
                } catch (err) {
                    contentDiv.innerHTML = '<p>Error loading content. Sites block some proxies.</p>';
                    console.error(err);
                }
            }

            function closeModal() {
                modal.style.display = 'none';
                contentDiv.innerHTML = ''; // Clear memory
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
