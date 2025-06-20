import requests

TR_JSON_URL = "https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/main/channels/raw/countries/tr.json"
IPTV_ORG_CHANNELS_URL = "https://iptv-org.github.io/api/channels.json"

def json_to_m3u(output_file="tv_garden_tr.m3u"):
    print("📥 Downloading Turkish channel list...")
    tr_channels = requests.get(TR_JSON_URL).json()

    print("📥 Downloading iptv-org metadata...")
    metadata = requests.get(IPTV_ORG_CHANNELS_URL).json()
    meta_map = {ch["id"]: ch for ch in metadata if ch.get("country") == "TR"}

    print("🧠 Merging and generating M3U...")
    m3u_lines = ["#EXTM3U"]
    seen = {}

    for channel in tr_channels:
        name = channel.get("name", "Unknown")
        tvg_id = channel.get("id", name)
        urls = channel.get("iptv_urls", [])

        # Match metadata by ID
        meta = meta_map.get(tvg_id, {})
        logo = meta.get("logo", "")
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

if __name__ == "__main__":
    json_to_m3u()
