import requests
from streamlink_helper import get_stream_url, get_stream_url_playwright

TR_JSON_URL = "https://raw.githubusercontent.com/famelack/famelack-channels/main/channels/raw/countries/tr.json"
IPTV_ORG_CHANNELS_URL = "https://iptv-org.github.io/api/channels.json"
DEFAULT_LOGO = "https://i.imgur.com/3pODQO3.png"  # Default TV icon
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def json_to_m3u(output_file="tv_garden_tr.m3u"):
    print("📥 Downloading Turkish channel list...")
    response = requests.get(TR_JSON_URL, headers=HEADERS)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"❌ Error: Could not download file. Status Code: {response.status_code}")
        print(f"   URL: {TR_JSON_URL}")
        return  # Stop execution here

    try:
        tr_channels = response.json()
    except Exception as e:
        print(f"❌ Error: Failed to decode JSON from {TR_JSON_URL}")
        print(f"   Exception: {e}")
        print(f"   Response Preview (first 500 chars):")
        print(response.text[:500])
        return

    print("📥 Downloading iptv-org metadata...")
    try:
        metadata_response = requests.get(IPTV_ORG_CHANNELS_URL, headers=HEADERS)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
    except Exception as e:
        print(f"❌ Error: Failed to download or decode metadata from {IPTV_ORG_CHANNELS_URL}")
        print(f"   Exception: {e}")
        return
    meta_map = {ch["id"]: ch for ch in metadata if ch.get("country") == "TR"}

    # Create a name-based lookup for better matching
    name_map = {ch["name"].lower(): ch for ch in metadata if ch.get("country") == "TR"}

    print("🧠 Merging and generating M3U...")
    m3u_lines = ["#EXTM3U"]
    seen = {}

    # Add streamlink based live channels
    live_channels = [
        {"name": "TV8", "url": "https://www.tv8.com.tr/canli-yayin", "id": "TV8.tr"},
        {"name": "Show TV", "url": "https://www.showtv.com.tr/canli-yayin", "id": "ShowTV.tr"},
        {"name": "ATV", "url": "https://www.atv.com.tr/canli-yayin", "id": "ATV.tr"},
        {"name": "Kanal D", "url": "https://www.kanald.com.tr/canli-yayin", "id": "KanalD.tr"},
        {"name": "Star TV", "url": "https://www.startv.com.tr/canli-yayin", "id": "StarTV.tr"}
    ]

    for live in live_channels:
        print(f"🔗 Fetching live stream for {live['name']}...")
        s_url = get_stream_url(live['url'])
        
        # Fallback naar Playwright als Streamlink faalt (voor Star TV en ATV)
        if not s_url:
            print(f"🔄 Streamlink failed for {live['name']}, trying Playwright...")
            s_url = get_stream_url_playwright(live['url'])

        if s_url:
            # Match metadata for logo
            meta = meta_map.get(live['id'], {})
            if not meta and live['name'].lower() in name_map:
                meta = name_map[live['name'].lower()]
            
            logo = meta.get("logo", DEFAULT_LOGO)
            group = "Turkey (Live)"
            
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{live["id"]}" tvg-logo="{logo}" group-title="{group}",{live["name"]}')
            m3u_lines.append(s_url)
            seen[f"{live['name']}_{s_url}"] = True

    for channel in tr_channels:
        name = channel.get("name", "Unknown")
        tvg_id = channel.get("id", name)
        urls = channel.get("iptv_urls", [])

        # Match metadata by ID
        meta = meta_map.get(tvg_id, {})

        # If no match by ID, try to match by name
        if not meta and name.lower() in name_map:
            meta = name_map[name.lower()]

        # If still no match, try partial name matching
        if not meta:
            for meta_name, meta_ch in name_map.items():
                if name.lower() in meta_name or meta_name in name.lower():
                    meta = meta_ch
                    break

        logo = meta.get("logo", DEFAULT_LOGO)  # Use default logo if none found
        group = "Turkey"

        for url in urls:
            if not url.endswith(".m3u8"):
                continue

            key = f"{name}_{url}"
            if key in seen:
                continue  # Avoid exact duplicates

            seen[key] = True
            m3u_lines.append(
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}'
            )
            m3u_lines.append(url)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"✅ M3U file generated: {output_file}")
    print(f"📊 Total channels: {len(seen)}")

if __name__ == "__main__":
    json_to_m3u()
