import json
import os

def json_to_m3u(json_file: str, output_file: str = "tv_garden_tr.m3u"):
    with open(json_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    m3u_lines = ['#EXTM3U']

    for channel in channels:
        name = channel.get("name", "Onbekend kanaal")
        for url in channel.get("iptv_urls", []):
            if url.endswith(".m3u8"):
                m3u_lines.append(f'#EXTINF:-1 tvg-id="{name}" group-title="Turkey",{name}')
                m3u_lines.append(url)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(m3u_lines))

    print(f"✅ M3U-bestand gegenereerd als: {output_file}")

if __name__ == "__main__":
    json_path = os.path.join("channels", "raw", "countries", "tr.json")
    json_to_m3u(json_path)
