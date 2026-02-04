import streamlink
import logging
import time

# Schakel logging van streamlink uit om de output schoon te houden
logging.getLogger("streamlink").setLevel(logging.ERROR)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

def get_stream_url(url, retries=6, delay=2):
    """
    Haalt de 'best' stream URL op voor een gegeven pagina URL met streamlink.
    Probeert het meerdere keren bij falen met verschillende User-Agents.
    """
    for attempt in range(1, retries + 1):
        try:
            # Kies een User-Agent op basis van de poging
            # Eerste 3 pogingen de eerste UA, daarna wisselen we
            ua_index = (attempt - 1) // 3 if attempt <= 3 else (attempt - 1) % len(USER_AGENTS)
            user_agent = USER_AGENTS[ua_index]
            
            # Initialiseer een Streamlink sessie
            session = streamlink.Streamlink()
            # Voeg headers toe om 403 errors te voorkomen
            session.set_option("http-headers", {
                "User-Agent": user_agent,
                "Referer": url
            })
            
            # Gebruik streamlink om de streams te vinden
            streams = session.streams(url)
            if streams:
                # We willen de 'best' stream
                best_stream = streams.get('best')
                if best_stream:
                    print(f"🔗 Found stream for {url} (Attempt {attempt} with UA index {ua_index})")
                    return best_stream.url
            
            print(f"⚠️ No stream found for {url} (Attempt {attempt}/{retries})")
            
        except Exception as e:
            print(f"❌ Error fetching stream for {url} (Attempt {attempt}/{retries}): {e}")
        
        if attempt < retries:
            time.sleep(delay)
            
    return None

if __name__ == "__main__":
    urls = [
        "https://www.tv8.com.tr/canli-yayin",
        "https://www.showtv.com.tr/canli-yayin",
        "https://www.atv.com.tr/canli-yayin",
        "https://www.kanald.com.tr/canli-yayin",
        "https://www.startv.com.tr/canli-yayin"
    ]
    
    for url in urls:
        print(f"Fetching {url}...")
        stream_url = get_stream_url(url)
        print(f"Result: {stream_url}")
