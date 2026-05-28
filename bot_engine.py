"""Motor del bot: TikTok Live + Claude + TTS. Sin dependencia de la GUI."""
import asyncio
import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

try:
    import anthropic
except ImportError:
    anthropic = None

import edge_tts
import pygame

from config_manager import build_catalog_text

AUDIO_DIR = "audio_cache"


class BotEngine:
    def __init__(self, config: dict, on_log: Callable = None, on_status: Callable = None):
        self.config = config
        self._on_log = on_log or (lambda m: None)
        self._on_status = on_status or (lambda b: None)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self.comment_q: queue.Queue = queue.Queue()
        self.ready_q: queue.Queue = queue.Queue()
        self._primera = True

    @property
    def running(self) -> bool:
        return self._running

    def log(self, msg: str):
        self._on_log(msg)

    def start(self):
        if self._running:
            return
        self._stop.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._running = False
        self._on_status(False)
        self.log("Bot detenido.")

    # ── hilo principal ─────────────────────────────────────────

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_main())
        except Exception as e:
            self.log(f"Error fatal: {e}")
        finally:
            self._running = False
            self._on_status(False)

    async def _async_main(self):
        api = self.config.get("api", {})
        settings = self.config.get("settings", {})

        self._tts_voice = api.get("tts_voice", "es-PE-CamilaNeural")
        self._el_api_key = api.get("elevenlabs_api_key", "").strip()
        self._el_voice_id = api.get("elevenlabs_voice_id", "").strip()
        if self._el_api_key and self._el_voice_id:
            self.log(f"TTS: ElevenLabs (voice_id={self._el_voice_id})")
        else:
            self.log(f"TTS: Edge TTS ({self._tts_voice})")
        self._username = api.get("tiktok_username", "")
        self._session_id = api.get("tiktok_session_id", "")
        self._catalog = build_catalog_text(self.config)
        self._segments = self.config.get("pitch_segments", [])
        self._store_name = self.config.get("store", {}).get("name", "la tienda")
        self._pause = float(settings.get("pause_between_segments", 0.4))
        self._test_mode = settings.get("test_mode", False)

        self._llm_provider = api.get("llm_provider", "anthropic")
        self._openai_api_key = api.get("openai_api_key", "").strip()

        if self._llm_provider == "openai":
            if not self._openai_api_key:
                self.log("ERROR: Falta la OpenAI API Key. Configurala en 'Configuracion API'.")
                self._running = False
                self._on_status(False)
                return
            self._claude = None
            self.log("IA: OpenAI (gpt-4o-mini)")
        else:
            anthropic_key = api.get("anthropic_api_key", "")
            if not anthropic_key:
                self.log("ERROR: Falta la Anthropic API Key. Configurala en 'Configuracion API'.")
                self._running = False
                self._on_status(False)
                return
            if anthropic is None:
                self.log("ERROR: Paquete 'anthropic' no instalado. Ejecuta: pip install anthropic")
                self._running = False
                self._on_status(False)
                return
            self._claude = anthropic.Anthropic(api_key=anthropic_key)
            self.log("IA: Anthropic (claude-haiku-4-5)")

        try:
            pygame.init()
            device = settings.get("audio_device", "")
            if device:
                pygame.mixer.init(devicename=device)
            else:
                pygame.mixer.init()
        except Exception as e:
            self.log(f"Advertencia de audio: {e}")

        os.environ.setdefault(
            "WHITELIST_AUTHENTICATED_SESSION_ID_HOST", "tiktok.eulerstream.com"
        )

        if self._test_mode:
            self.log("[MODO PRUEBA] Comentarios simulados, sin conexion real a TikTok.")
            threading.Thread(target=self._simulate_comments, daemon=True).start()
        else:
            threading.Thread(target=self._tiktok_thread, daemon=True).start()

        self._on_status(True)
        await self._pitch_loop()

    # ── TikTok ─────────────────────────────────────────────────

    def _tiktok_thread(self):
        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent
        except ImportError:
            self.log("ERROR: TikTokLive no instalado. Ejecuta: pip install TikTokLive==6.6.5")
            return

        while not self._stop.is_set():
            try:
                client = TikTokLiveClient(unique_id=self._username)
                if self._session_id:
                    client._web.set_session(self._session_id, "useast1a")

                @client.on(ConnectEvent)
                async def _connect(event):
                    self.log(f"Conectado: {self._username} (Room {event.room_id})")

                @client.on(CommentEvent)
                async def _comment(event):
                    self.comment_q.put((event.user.unique_id, event.comment))

                @client.on(DisconnectEvent)
                async def _disconnect(_):
                    self.log("Desconectado del live.")

                client.run()
            except Exception as e:
                if not self._stop.is_set():
                    self.log(f"TikTok error, reintentando en 15s: {e}")
                    time.sleep(15)

    def _simulate_comments(self):
        samples = [
            ("usuario_1", "cuanto cuesta?"),
            ("usuario_2", "tienen envios a provincia?"),
            ("usuario_3", "para que edad es?"),
            ("usuario_4", "jajaja que bueno"),
            ("usuario_5", "como hago mi pedido?"),
        ]
        time.sleep(10)
        for u, c in samples:
            if self._stop.is_set():
                break
            time.sleep(7)
            self.comment_q.put((u, c))
            self.log(f"[PRUEBA] @{u}: {c}")

    # ── TTS & audio ────────────────────────────────────────────

    def _tts_clean(self, text: str) -> str:
        text = re.sub(
            r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FAFF]+", "", text
        )
        text = re.sub(r"[*_~`#|]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    async def _tts(self, text: str, path: str):
        clean = self._tts_clean(text)
        if self._el_api_key and self._el_voice_id:
            await self._tts_elevenlabs(clean, path)
        else:
            await self._tts_edge(clean, path)

    async def _tts_edge(self, clean: str, path: str):
        for attempt in range(1, 4):
            try:
                await edge_tts.Communicate(clean, self._tts_voice).save(path)
                return
            except Exception as e:
                if attempt == 3:
                    raise
                self.log(f"TTS Edge error intento {attempt}/3: {e}")
                await asyncio.sleep(3)

    async def _tts_elevenlabs(self, clean: str, path: str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._el_voice_id}"
        payload = json.dumps({
            "text": clean,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }).encode("utf-8")
        headers = {
            "xi-api-key": self._el_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        loop = asyncio.get_event_loop()
        for attempt in range(1, 4):
            try:
                def _fetch():
                    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        return resp.read()
                audio_bytes = await loop.run_in_executor(None, _fetch)
                with open(path, "wb") as f:
                    f.write(audio_bytes)
                return
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore")
                self.log(f"ElevenLabs HTTP {e.code}: {body[:120]}")
                if e.code in (401, 403):
                    self.log("API Key o Voice ID invalidos. Revisa la configuracion.")
                    raise
                if attempt == 3:
                    raise
                await asyncio.sleep(3)
            except Exception as e:
                if attempt == 3:
                    raise
                self.log(f"ElevenLabs error intento {attempt}/3: {e}")
                await asyncio.sleep(3)

    async def _play(self, path: str):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        try:
            while pygame.mixer.music.get_busy():
                if self._stop.is_set():
                    pygame.mixer.music.stop()
                    return
                await asyncio.sleep(0.05)
                while not self.comment_q.empty():
                    u, c = self.comment_q.get_nowait()
                    asyncio.create_task(self._handle_comment(u, c))
        except asyncio.CancelledError:
            pygame.mixer.music.stop()
            raise

    # ── LLM helpers ────────────────────────────────────────────

    def _openai_chat(self, system: str, user_msg: str, max_tokens: int) -> str:
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        }).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload, headers=headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()

    def _is_product_question(self, comment: str) -> bool:
        system = (
            "Clasifica si el comentario es pregunta sobre productos, precios, "
            "beneficios, disponibilidad, tienda, ubicacion, envios o delivery. "
            "Responde unicamente SI o NO."
        )
        try:
            if self._llm_provider == "openai":
                text = self._openai_chat(system, comment, 5)
            else:
                r = self._claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=5,
                    system=system,
                    messages=[{"role": "user", "content": comment}],
                )
                text = r.content[0].text
            return "SI" in text.upper()
        except Exception:
            return False

    def _generate_response(self, user: str, comment: str) -> str:
        system = (
            f"Eres la vendedora de {self._store_name} en un live de TikTok. "
            "Solo texto plano, sin emojis, sin asteriscos, sin guiones. "
            "Maximo 2 oraciones cortas. Tono amigable. "
            "Para contacto di siempre 'escribenos al verdecito en pantalla'.\n\n"
            f"CATALOGO:\n{self._catalog}"
        )
        user_msg = f"{user} pregunta: {comment}. Responde en voz alta."
        try:
            if self._llm_provider == "openai":
                return self._openai_chat(system, user_msg, 130)
            else:
                r = self._claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=130,
                    system=system,
                    messages=[{"role": "user", "content": user_msg}],
                )
                return r.content[0].text.strip()
        except Exception:
            return "Escribenos al verdecito para mas informacion."

    async def _handle_comment(self, user: str, comment: str):
        loop = asyncio.get_event_loop()
        self.log(f"@{user}: {comment}")
        is_q = await loop.run_in_executor(None, self._is_product_question, comment)
        if not is_q:
            return
        response = await loop.run_in_executor(None, self._generate_response, user, comment)
        self.log(f"  -> {response}")
        oral = f"{user} pregunta: {comment}. {response}"
        path = os.path.join(AUDIO_DIR, f"resp_{int(time.time()*1000)}.mp3")
        await self._tts(oral, path)
        self.ready_q.put(path)

    async def _play_responses(self):
        while not self.ready_q.empty():
            path = self.ready_q.get_nowait()
            try:
                if self._primera:
                    esp = os.path.join(AUDIO_DIR, "esperen.mp3")
                    if os.path.exists(esp):
                        await self._play(esp)
                    pygame.mixer.music.unload()
                    self._primera = False
                await self._play(path)
            finally:
                pygame.mixer.music.unload()
                if os.path.exists(path):
                    os.remove(path)

    # ── bucle pitch ────────────────────────────────────────────

    async def _pregen_pitch(self):
        os.makedirs(AUDIO_DIR, exist_ok=True)
        missing = [
            s for s in self._segments
            if not os.path.exists(os.path.join(AUDIO_DIR, f"{s['id']}.mp3"))
        ]
        if not missing:
            self.log("Audios del pitch ya generados.")
            return
        self.log(f"Generando {len(missing)} audio(s) del pitch...")
        for s in missing:
            await self._tts(s["text"], os.path.join(AUDIO_DIR, f"{s['id']}.mp3"))
            self.log(f"  Listo: {s['id']}")
        esp = os.path.join(AUDIO_DIR, "esperen.mp3")
        if not os.path.exists(esp):
            await self._tts("Esperen un momento...", esp)
        self.log("Pitch listo.")

    async def _pitch_loop(self):
        if not self._segments:
            self.log("Sin segmentos de pitch. Configuralos en la pestana 'Pitch'.")
            while not self._stop.is_set():
                await asyncio.sleep(1)
            return

        await self._pregen_pitch()
        self.log("Pitch iniciado. Bot en marcha.")
        idx = 0
        while not self._stop.is_set():
            seg = self._segments[idx]
            path = os.path.join(AUDIO_DIR, f"{seg['id']}.mp3")
            if not os.path.exists(path):
                await self._tts(seg["text"], path)
            self.log(f"Reproduciendo: {seg['id']}")
            self._primera = True
            await self._play(path)
            while not self.comment_q.empty():
                u, c = self.comment_q.get_nowait()
                asyncio.create_task(self._handle_comment(u, c))
            await self._play_responses()
            await asyncio.sleep(self._pause)
            idx = (idx + 1) % len(self._segments)
