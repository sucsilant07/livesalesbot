"""Script de prueba de conexion TikTok — carga credenciales desde livesalesbot_config.json."""
import asyncio
import os
import traceback

from config_manager import load_config

config = load_config()
api = config.get("api", {})

SESSION_ID = api.get("tiktok_session_id", "")
USERNAME   = api.get("tiktok_username", "").lstrip("@")

if not SESSION_ID or not USERNAME:
    print("ERROR: Configura TIKTOK_USERNAME y TIKTOK_SESSION_ID en la GUI (python main.py).")
    exit(1)

os.environ["WHITELIST_AUTHENTICATED_SESSION_ID_HOST"] = "tiktok.eulerstream.com"

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent


async def test():
    client = TikTokLiveClient(unique_id=USERNAME)
    client._web.set_session(SESSION_ID, "useast1a")

    @client.on(ConnectEvent)
    async def al_conectar(event: ConnectEvent):
        print(f"CONECTADO al live! Room ID: {event.room_id}")

    @client.on(CommentEvent)
    async def al_comentario(event: CommentEvent):
        nombre = event.user.unique_id if event.user else "?"
        print(f"Comentario de {nombre}: {event.comment}")

    @client.on(DisconnectEvent)
    async def al_desconectar(_):
        print("Desconectado.")

    print(f"Intentando conectar a @{USERNAME}...")
    try:
        await client.connect()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()


asyncio.run(test())
