"""Carga, guarda y construye el catálogo desde livesalesbot_config.json."""
import copy
import json
import os

CONFIG_FILE = "livesalesbot_config.json"

DEFAULT_CONFIG = {
    "api": {
        "tiktok_username": "",
        "tiktok_session_id": "",
        "anthropic_api_key": "",
        "tts_voice": "es-PE-CamilaNeural",
        "elevenlabs_api_key": "",
        "elevenlabs_voice_id": "",
        "llm_provider": "anthropic",
        "openai_api_key": "",
    },
    "store": {
        "name": "",
        "description": "",
        "location": "",
        "whatsapp": "",
        "extra_info": "",
    },
    "products": [],
    "pitch_segments": [],
    "settings": {
        "test_mode": False,
        "pause_between_segments": 0.4,
        "audio_device": "",
    },
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return _deep_merge(copy.deepcopy(DEFAULT_CONFIG), loaded)
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def build_catalog_text(config: dict) -> str:
    store = config.get("store", {})
    products = config.get("products", [])
    parts: list[str] = []

    if store.get("name"):
        parts.append(f"TIENDA: {store['name']}")
    if store.get("description"):
        parts.append(store["description"])
    if store.get("whatsapp"):
        parts.append(f"Pedidos y consultas por WhatsApp: {store['whatsapp']}")
    if store.get("location"):
        parts.append(f"Ubicacion: {store['location']}")

    if products:
        parts.append("\nPRODUCTOS:")
        for i, p in enumerate(products, 1):
            block = [f"\n{i}. {p.get('name', 'Producto')}"]
            if p.get("price"):
                block.append(f"   Precio: {p['price']}")
            if p.get("for_whom"):
                block.append(f"   Para: {p['for_whom']}")
            if p.get("description"):
                block.append(f"   Descripcion: {p['description']}")
            if p.get("benefits"):
                block.append(f"   Beneficios: {p['benefits']}")
            parts.append("\n".join(block))

    if store.get("extra_info"):
        parts.append(f"\n{store['extra_info']}")

    return "\n".join(parts)


def _deep_merge(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = _deep_merge(base[k], v)
        else:
            base[k] = v
    return base
