import json
import os
import requests

def json_to_m3u(json_file: str, output_file: str = "tv_garden_tr.m3u"):
    # Load main Turkish channel list with URLs
    with open(json_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    # Fetch extra metadata from iptv-org API
    print("🔗 Downloading metadata from iptv-org API...")
    metadata = []
    try:
        res = requests.get("https://iptv-org.github.io/api/channels.json")
        res.raise_for_status()
        metadata = res.json()
    except Exception as e:
        print(f"⚠️ Failed to fetch iptv-org metadata: {e}")

    # Build a map of channel ID → logo
    logo_map = {
        ch["id"]: ch.get("logo")
        for ch in metadata
        if ch.get("country") == "TR"
    }

    m3u_lines = ['#EXTM3U']

    for channel in channels:
        name = channel.get("name", "Onbekend kanaal")
        tvg_id = channel.get("id", name)
        logo = logo_map.get(tvg_id, "")
        group = "Turkey"

        for url in channel.get("iptv_urls", []):
            if url.endswith(".m3u8"):
                m3u_lines.append(
                    f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}'
                )
                m3u_lines.append(url)

    # Write M3U file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(m3u_lines))

    print(f"✅ M3U-bestand gegenereerd als: {output_file}")

if __name__ == "__main__":
    json_path = os.path.join("channels", "raw", "countries", "tr.json")
    json_to_m3u(json_path)
