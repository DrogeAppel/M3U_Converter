import requests

TR_JSON_URL = "https://raw.githubusercontent.com/famelack/famelack-channels/main/channels/raw/countries/tr.json"
IPTV_ORG_CHANNELS_URL = "https://iptv-org.github.io/api/channels.json"
DEFAULT_LOGO = "https://i.imgur.com/3pODQO3.png"  # Default TV icon


def json_to_m3u(output_file="tv_garden_tr.m3u"):
    print("📥 Downloading Turkish channel list...")
    response = requests.get(TR_JSON_URL)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"❌ Error: Could not download file. Status Code: {response.status_code}")
        print(f"   URL: {TR_JSON_URL}")
        return  # Stop execution here

    tr_channels = response.json()

    print("📥 Downloading iptv-org metadata...")
    metadata = requests.get(IPTV_ORG_CHANNELS_URL).json()
    meta_map = {ch["id"]: ch for ch in metadata if ch.get("country") == "TR"}

    # Create a name-based lookup for better matching
    name_map = {ch["name"].lower(): ch for ch in metadata if ch.get("country") == "TR"}

    print("🧠 Merging and generating M3U...")
    m3u_lines = ["#EXTM3U"]
    seen = {}

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
