import streamlink
import logging
import asyncio
from playwright.async_api import async_playwright

# Schakel logging van streamlink uit om de output schoon te houden
logging.getLogger("streamlink").setLevel(logging.ERROR)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

async def get_stream_url_playwright(url, wait_time=8):
    """
    Haalt de m3u8 URL op door de pagina te laden met Playwright en network requests te inspecteren.
    Handig voor zenders met complexe beveiliging zoals Star TV of ATV.
    """
    captured_urls = []

    async def handle_route(route):
        if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()

    async def handle_request(request):
        u = request.url
        if ".m3u8" in u.lower():
            # Check for keywords that indicate it's a stream playlist and not just an ad
            keywords = ["master", "playlist", "chunklist", "live", "stream"]
            if any(k in u.lower() for k in keywords) and u not in captured_urls:
                captured_urls.append(u)
            elif u not in captured_urls:
                captured_urls.append(u)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=USER_AGENTS[0],
                viewport={"width": 1280, "height": 720},
                locale="tr-TR",
                timezone_id="Europe/Istanbul"
            )
            page = await context.new_page()
            
            # Blokkeer afbeeldingen en andere onnodige bronnen om laden te versnellen
            # Ook ads en analytics blokkeren kan helpen
            await page.route("**/*", handle_route)
            
            page.on("request", handle_request)
            
            print(f"🌐 [Playwright] Loading {url}...")
            try:
                # 'commit' is de allersnelste wacht-optie in Playwright (zodra de response ontvangen is)
                await page.goto(url, wait_until="commit", timeout=30000)
            except Exception as e:
                print(f"⚠️ [Playwright] Goto warning for {url}: {e} (continuing anyway)")

            # Wacht even voor de player om te initialiseren en requests te doen
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < wait_time:
                if captured_urls:
                    # Als we al een master playlist hebben, kunnen we direct stoppen
                    if any("master" in u.lower() for u in captured_urls):
                        print(f"✅ [Playwright] Master stream found after {int(asyncio.get_event_loop().time() - start_time)}s")
                        break
                    # Als we tenminste één m3u8 hebben en al 5 seconden hebben gewacht, is het waarschijnlijk de goede
                    if asyncio.get_event_loop().time() - start_time > 5:
                        print(f"✅ [Playwright] Stream found after {int(asyncio.get_event_loop().time() - start_time)}s")
                        break
                await asyncio.sleep(1)
            
            # Probeer op een play knop te klikken als we nog niks hebben
            if not captured_urls:
                try:
                    play_buttons = await page.query_selector_all("button")
                    for btn in play_buttons:
                        if await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(2)
                            if captured_urls: break
                except:
                    pass

            await browser.close()
    except Exception as e:
        print(f"❌ [Playwright] Error for {url}: {e}")

    if captured_urls:
        for u in captured_urls:
            if "master" in u.lower():
                return u
        return captured_urls[0]
    
    return None

def _get_streamlink_url_sync(url, retries=3, delay=2):
    """
    Synchronous helper for streamlink to be run in a thread.
    Lowered retries to 3 as requested.
    """
    for attempt in range(1, retries + 1):
        try:
            ua_index = (attempt - 1) % len(USER_AGENTS)
            user_agent = USER_AGENTS[ua_index]
            
            session = streamlink.Streamlink()
            session.set_option("http-headers", {
                "User-Agent": user_agent,
                "Referer": url
            })
            
            streams = session.streams(url)
            if streams:
                best_stream = streams.get('best')
                if best_stream:
                    print(f"🔗 Found stream for {url} (Attempt {attempt} with UA index {ua_index})")
                    return best_stream.url
            
            print(f"⚠️ No stream found for {url} (Attempt {attempt}/{retries})")
            
        except Exception as e:
            print(f"❌ Error fetching stream for {url} (Attempt {attempt}/{retries}): {e}")
        
        if attempt < retries:
            import time
            time.sleep(delay)
            
    return None

async def get_stream_url(url, retries=3, delay=2):
    """
    Asynchronous wrapper for streamlink.
    """
    return await asyncio.to_thread(_get_streamlink_url_sync, url, retries, delay)

async def get_stream_url_combined(url):
    """
    Tries Streamlink first, and if it fails, falls back to Playwright.
    Or can be modified to run them concurrently if speed is the main concern.
    Given the user's request 'maybe direct so one streamlink and directly the playwright',
    we can run them concurrently and return the first one that succeeds.
    """
    # Start both tasks concurrently
    tasks = [
        asyncio.create_task(get_stream_url(url)),
        asyncio.create_task(get_stream_url_playwright(url))
    ]
    
    # We want the first one that returns a valid URL
    # But get_stream_url might return None if it fails.
    # We'll wait for them to finish and take the first non-None result.
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    
    for task in done:
        result = task.result()
        if result:
            # Cancel the other task if one succeeded
            for p in pending:
                p.cancel()
            return result
            
    # If the first one finished but returned None, wait for the others
    if pending:
        done2, pending2 = await asyncio.wait(pending, return_when=asyncio.ALL_COMPLETED)
        for task in done2:
            result = task.result()
            if result:
                return result
                
    return None
