import streamlink
import logging
import time
from playwright.sync_api import sync_playwright

# Schakel logging van streamlink uit om de output schoon te houden
logging.getLogger("streamlink").setLevel(logging.ERROR)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

def get_stream_url_playwright(url, wait_time=15):
    """
    Haalt de m3u8 URL op door de pagina te laden met Playwright en network requests te inspecteren.
    Handig voor zenders met complexe beveiliging zoals Star TV of ATV.
    """
    captured_urls = []

    def handle_request(request):
        u = request.url
        if ".m3u8" in u.lower() and "master" in u.lower(): # Vaak is master degene die we willen
            captured_urls.append(u)
        elif ".m3u8" in u.lower() and u not in captured_urls:
            captured_urls.append(u)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENTS[0],
                viewport={"width": 1280, "height": 720},
                locale="tr-TR",
                timezone_id="Europe/Istanbul"
            )
            page = context.new_page()
            page.on("request", handle_request)
            
            print(f"🌐 [Playwright] Loading {url}...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wacht even voor de player om te initialiseren en requests te doen
            time.sleep(wait_time)
            
            # Probeer op een play knop te klikken als die er is (vaak nodig voor sommige zenders)
            try:
                # Zoek naar algemene play knoppen
                play_buttons = page.query_selector_all("button")
                for btn in play_buttons:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(2)
            except:
                pass

            browser.close()
    except Exception as e:
        print(f"❌ [Playwright] Error for {url}: {e}")

    if captured_urls:
        # Filter op meest waarschijnlijke link (vaak de laatste of degene met 'master')
        for u in captured_urls:
            if "master" in u.lower():
                return u
        return captured_urls[0]
    
    return None

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
