import streamlink
import logging

# Schakel logging van streamlink uit om de output schoon te houden
logging.getLogger("streamlink").setLevel(logging.ERROR)

def get_stream_url(url):
    """
    Haalt de 'best' stream URL op voor een gegeven pagina URL met streamlink.
    """
    try:
        # Initialiseer een Streamlink sessie
        session = streamlink.Streamlink()
        # Voeg headers toe om 403 errors te voorkomen
        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": url
        })
        
        # Gebruik streamlink om de streams te vinden
        streams = session.streams(url)
        if not streams:
            return None
        
        # We willen de 'best' stream
        best_stream = streams.get('best')
        if best_stream:
            return best_stream.url
        return None
    except Exception as e:
        print(f"Error fetching stream for {url}: {e}")
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
