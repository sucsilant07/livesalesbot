"""Debug: descarga el HTML del live de TikTok y busca el room_id."""
import asyncio
import re

from config_manager import load_config

config = load_config()
api = config.get("api", {})

SESSION_ID = api.get("tiktok_session_id", "")
USERNAME   = api.get("tiktok_username", "").lstrip("@")

if not SESSION_ID or not USERNAME:
    print("ERROR: Configura TIKTOK_USERNAME y TIKTOK_SESSION_ID en la GUI (python main.py).")
    exit(1)

from TikTokLive import TikTokLiveClient


async def test():
    c = TikTokLiveClient(unique_id=USERNAME)
    c.http.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    c.http.cookies.set("sessionid",    SESSION_ID, domain=".tiktok.com")
    c.http.cookies.set("sessionid_ss", SESSION_ID, domain=".tiktok.com")

    html = await c.http.get_livestream_page_html(USERNAME)
    print(f"Tamano HTML: {len(html)} chars\n")

    for pattern in [r"room_id", r"roomId", r"liveRoomId", r"RoomId"]:
        matches = [
            (m.start(), html[max(0, m.start() - 10) : m.end() + 40])
            for m in re.finditer(pattern, html)
        ]
        if matches:
            print(f"--- Patron '{pattern}' ({len(matches)} ocurrencias) ---")
            for pos, ctx in matches[:5]:
                print(f"  pos {pos}: {repr(ctx)}")
        else:
            print(f"--- Patron '{pattern}': NO encontrado ---")
        print()


asyncio.run(test())
