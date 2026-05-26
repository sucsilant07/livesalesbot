"""Interfaz grafica de LiveSalesBot."""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from bot_engine import BotEngine
from config_manager import load_config, save_config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ════════════════════════════════════════════════════════════════
#  Textos de ayuda
# ════════════════════════════════════════════════════════════════

HELP_TEXTS: dict[str, dict] = {
    "tiktok_username": {
        "title": "Como obtener tu usuario de TikTok",
        "body": (
            "Tu nombre de usuario de TikTok es el que aparece con @ en tu perfil.\n\n"
            "PASOS:\n"
            "1. Abre TikTok (app o tiktok.com)\n"
            "2. Ve a tu perfil\n"
            "3. Copia tu @usuario exactamente como aparece\n\n"
            "Ejemplo: @mi_tienda_oficial\n\n"
            "IMPORTANTE: Incluye el simbolo @ al inicio."
        ),
    },
    "tiktok_session_id": {
        "title": "Como obtener el Session ID de TikTok",
        "body": (
            "Necesitas la extension 'Cookie-Editor' en Chrome o Edge.\n\n"
            "PASOS:\n"
            "1. Instala 'Cookie-Editor' desde la tienda de extensiones de Chrome\n\n"
            "2. Ve a tiktok.com en ese mismo navegador e INICIA SESION\n"
            "   con la cuenta que usaras para el live\n\n"
            "3. Haz clic en el icono de Cookie-Editor (arriba a la derecha)\n\n"
            "4. En la lista de cookies, busca la que se llama exactamente: sessionid\n\n"
            "5. Haz clic en el valor y copialo\n"
            "   (es una cadena larga de letras y numeros)\n\n"
            "6. Pegalo en el campo 'Session ID' del bot\n\n"
            "NOTA: El sessionid caduca cada cierto tiempo.\n"
            "Si el bot falla por autenticacion, repite este proceso."
        ),
    },
    "anthropic_api_key": {
        "title": "Como obtener la Anthropic API Key",
        "body": (
            "La API Key de Anthropic permite al bot usar la IA de Claude.\n\n"
            "PASOS:\n"
            "1. Ve a: console.anthropic.com\n\n"
            "2. Crea una cuenta gratuita o inicia sesion\n\n"
            "3. En el menu lateral izquierdo, haz clic en 'API Keys'\n\n"
            "4. Haz clic en el boton 'Create Key'\n\n"
            "5. Ponle un nombre (ej: LiveSalesBot) y confirma\n\n"
            "6. Copia la clave — empieza con sk-ant-api03-...\n"
            "   IMPORTANTE: solo puedes verla una vez.\n"
            "   Guardala en un lugar seguro antes de cerrar.\n\n"
            "7. Pegala en el campo 'Anthropic API Key' del bot\n\n"
            "COSTO: Anthropic cobra por uso. El bot usa Claude Haiku,\n"
            "el modelo mas economico (~$0.25 por millon de tokens).\n"
            "Necesitas un metodo de pago activo en tu cuenta."
        ),
    },
    "tts_voice": {
        "title": "Seleccion de voz (TTS)",
        "body": (
            "El bot convierte texto a voz usando Microsoft Edge TTS.\n\n"
            "CODIGO DE PAISES:\n"
            "  PE = Peru\n"
            "  MX = Mexico\n"
            "  ES = Espana\n"
            "  AR = Argentina\n"
            "  CO = Colombia\n"
            "  CL = Chile\n\n"
            "TIPOS DE VOZ:\n"
            "  Neural = voz sintetizada de alta calidad\n\n"
            "EJEMPLOS:\n"
            "  es-PE-CamilaNeural -> voz femenina peruana\n"
            "  es-PE-AlexNeural   -> voz masculina peruana\n"
            "  es-MX-DaliaNeural  -> voz femenina mexicana\n\n"
            "Puedes escuchar muestras en:\n"
            "learn.microsoft.com/azure/cognitive-services/speech-service/language-support"
        ),
    },
    "audio_device": {
        "title": "Dispositivo de audio",
        "body": (
            "Selecciona por donde saldra el audio del bot.\n\n"
            "OPCIONES:\n"
            "- Vacio = usa el altavoz predeterminado del sistema\n\n"
            "- Para transmitir con OBS usando VB-Audio:\n"
            "  Escribe exactamente:\n"
            "  CABLE Input (VB-Audio Virtual Cable)\n\n"
            "COMO VER LOS NOMBRES DISPONIBLES:\n"
            "1. Ve a Configuracion > Sistema > Sonido\n"
            "2. En 'Dispositivos de salida' veras los nombres\n"
            "   Copialos exactamente como aparecen.\n\n"
            "IMPORTANTE: Si el nombre es incorrecto, el bot\n"
            "usara el dispositivo predeterminado."
        ),
    },
}


# ════════════════════════════════════════════════════════════════
#  Ventana de ayuda
# ════════════════════════════════════════════════════════════════

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, parent, topic: str):
        super().__init__(parent)
        info = HELP_TEXTS.get(topic, {"title": "Ayuda", "body": "Sin informacion disponible."})
        self.title(info["title"])
        self.geometry("520x500")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        ctk.CTkLabel(
            self, text=info["title"],
            font=ctk.CTkFont(size=15, weight="bold"),
            wraplength=480, anchor="w",
        ).pack(fill="x", padx=20, pady=(20, 10))

        box = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        box.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        box.insert("end", info["body"])
        box.configure(state="disabled")

        ctk.CTkButton(self, text="Cerrar", width=120, command=self.destroy).pack(pady=(0, 16))


# ════════════════════════════════════════════════════════════════
#  Dialogo: agregar / editar producto
# ════════════════════════════════════════════════════════════════

class ProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, product: dict | None = None):
        super().__init__(parent)
        self.result: dict | None = None
        p = product or {}
        self.title("Editar producto" if product else "Agregar producto")
        self.geometry("500x500")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        self._vars: dict[str, tk.StringVar] = {}
        self._boxes: dict[str, ctk.CTkTextbox] = {}

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=(16, 0))

        simple = [
            ("Nombre del producto *", "name"),
            ("Precio  (ej: S/ 99 o $19.99)", "price"),
            ("Para quien  (ej: ninos, adultos, todas las edades)", "for_whom"),
        ]
        for lbl, key in simple:
            ctk.CTkLabel(scroll, text=lbl, anchor="w").pack(fill="x", pady=(6, 2))
            var = tk.StringVar(value=p.get(key, ""))
            ctk.CTkEntry(scroll, textvariable=var).pack(fill="x")
            self._vars[key] = var

        multi = [
            ("Descripcion breve", "description"),
            ("Beneficios", "benefits"),
        ]
        for lbl, key in multi:
            ctk.CTkLabel(scroll, text=lbl, anchor="w").pack(fill="x", pady=(10, 2))
            box = ctk.CTkTextbox(scroll, height=72, wrap="word")
            box.insert("end", p.get(key, ""))
            box.pack(fill="x")
            self._boxes[key] = box

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(bar, text="Cancelar", fg_color="gray40", width=110,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text="Guardar", width=110, command=self._save).pack(side="right")

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Campo requerido", "El nombre del producto es obligatorio.", parent=self)
            return
        data: dict = {}
        for k, v in self._vars.items():
            data[k] = v.get().strip()
        for k, b in self._boxes.items():
            data[k] = b.get("1.0", "end").strip()
        self.result = data
        self.destroy()


# ════════════════════════════════════════════════════════════════
#  Dialogo: agregar / editar segmento de pitch
# ════════════════════════════════════════════════════════════════

class SegmentDialog(ctk.CTkToplevel):
    def __init__(self, parent, segment: dict | None = None, existing_ids: list | None = None):
        super().__init__(parent)
        self.result: dict | None = None
        s = segment or {}
        self._existing = existing_ids or []
        self._edit_id = s.get("id", "")
        self.title("Editar segmento" if segment else "Agregar segmento")
        self.geometry("540x430")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="ID del segmento  (sin espacios, ej: intro, producto_1, cierre)",
                     anchor="w").pack(fill="x", pady=(0, 2))
        self._id_var = tk.StringVar(value=s.get("id", ""))
        ctk.CTkEntry(frame, textvariable=self._id_var).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(frame, text="Texto del segmento  (este texto se convertira en audio)",
                     anchor="w").pack(fill="x", pady=(0, 2))
        self._text_box = ctk.CTkTextbox(frame, wrap="word")
        self._text_box.insert("end", s.get("text", ""))
        self._text_box.pack(fill="both", expand=True, pady=(0, 12))

        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.pack(fill="x")
        ctk.CTkButton(bar, text="Cancelar", fg_color="gray40", width=110,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text="Guardar", width=110, command=self._save).pack(side="right")

    def _save(self):
        seg_id = self._id_var.get().strip().replace(" ", "_")
        text = self._text_box.get("1.0", "end").strip()
        if not seg_id:
            messagebox.showwarning("Campo requerido", "El ID es obligatorio.", parent=self)
            return
        if not text:
            messagebox.showwarning("Campo requerido", "El texto es obligatorio.", parent=self)
            return
        if seg_id in self._existing and seg_id != self._edit_id:
            messagebox.showwarning("ID duplicado", f"Ya existe un segmento con el ID '{seg_id}'.", parent=self)
            return
        self.result = {"id": seg_id, "text": text}
        self.destroy()


# ════════════════════════════════════════════════════════════════
#  Barra lateral
# ════════════════════════════════════════════════════════════════

_NAV = [
    ("Panel Principal", "panel"),
    ("Configuracion API", "apis"),
    ("Mi Tienda", "tienda"),
    ("Productos", "productos"),
    ("Pitch", "pitch"),
    ("Ajustes", "ajustes"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_nav: Callable, on_start: Callable, on_stop: Callable):
        super().__init__(master, width=196, corner_radius=0)
        self.pack_propagate(False)
        self._btns: dict[str, ctk.CTkButton] = {}

        ctk.CTkLabel(
            self, text="LiveSalesBot",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(pady=(24, 2))

        self._status_lbl = ctk.CTkLabel(
            self, text="Detenido", text_color="#e74c3c",
            font=ctk.CTkFont(size=12),
        )
        self._status_lbl.pack(pady=(0, 18))

        sep = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep.pack(fill="x", padx=12, pady=(0, 10))

        for label, key in _NAV:
            btn = ctk.CTkButton(
                self, text=label, anchor="w", height=36,
                fg_color="transparent",
                text_color=("gray10", "gray85"),
                hover_color=("gray80", "gray28"),
                command=lambda k=key: on_nav(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._btns[key] = btn

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        sep2 = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep2.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            self, text="Iniciar Bot", height=38,
            fg_color="#27ae60", hover_color="#1e8449",
            command=on_start,
        ).pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(
            self, text="Detener Bot", height=38,
            fg_color="#c0392b", hover_color="#922b21",
            command=on_stop,
        ).pack(fill="x", padx=10, pady=(0, 20))

    def set_active(self, key: str):
        for k, btn in self._btns.items():
            active = k == key
            btn.configure(fg_color=("gray75", "gray30") if active else "transparent")

    def set_running(self, running: bool):
        if running:
            self._status_lbl.configure(text="En marcha", text_color="#27ae60")
        else:
            self._status_lbl.configure(text="Detenido", text_color="#e74c3c")


# ════════════════════════════════════════════════════════════════
#  Pagina: Panel Principal
# ════════════════════════════════════════════════════════════════

class PanelPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Panel Principal",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 8))

        self._log = ctk.CTkTextbox(
            self, state="disabled", wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self._log.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 10))

        ctk.CTkButton(
            self, text="Limpiar log", fg_color="gray40", width=130, height=32,
            command=self._clear,
        ).grid(row=2, column=0, sticky="e", padx=24, pady=(0, 16))

    def append_log(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", f"{msg}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")


# ════════════════════════════════════════════════════════════════
#  Pagina: Configuracion API
# ════════════════════════════════════════════════════════════════

class APIPage(ctk.CTkFrame):
    def __init__(self, master: "App"):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._app = master
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="Configuracion de APIs",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            self,
            text="Ingresa tus credenciales para conectar el bot a TikTok y a la IA de Claude.",
            text_color="gray60", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=24)
        form.columnconfigure(1, weight=1)

        api = self._app.config_data.get("api", {})
        self._vars: dict[str, tk.StringVar] = {}

        # Campo: usuario TikTok
        self._make_field(form, 0, "Usuario de TikTok", "tiktok_username", api, masked=False, help_topic="tiktok_username")
        # Campo: session ID TikTok
        self._make_field(form, 1, "Session ID de TikTok", "tiktok_session_id", api, masked=True, help_topic="tiktok_session_id")
        # Campo: API Key Anthropic
        self._make_field(form, 2, "Anthropic API Key", "anthropic_api_key", api, masked=True, help_topic="anthropic_api_key")

        # Voz TTS
        row = 3
        ctk.CTkLabel(form, text="Voz TTS", anchor="w", width=210).grid(
            row=row, column=0, sticky="w", pady=12, padx=(0, 12))
        voices = [
            "es-PE-CamilaNeural", "es-PE-AlexNeural",
            "es-MX-DaliaNeural", "es-MX-JorgeNeural",
            "es-ES-ElviraNeural", "es-AR-ElenaNeural",
            "es-CO-SalomeNeural", "es-CL-CatalinaNeural",
        ]
        self._voice_var = tk.StringVar(value=api.get("tts_voice", voices[0]))
        ctk.CTkComboBox(form, values=voices, variable=self._voice_var, width=360).grid(
            row=row, column=1, sticky="w", pady=12)
        ctk.CTkButton(form, text="?", width=34,
                      command=lambda: HelpWindow(self, "tts_voice")).grid(
            row=row, column=2, padx=(8, 0), pady=12)

        ctk.CTkButton(
            self, text="Guardar configuracion", height=40,
            command=self._save,
        ).grid(row=3, column=0, sticky="w", padx=24, pady=(28, 0))

    def _make_field(self, form, row: int, label: str, key: str, api: dict,
                    masked: bool, help_topic: str):
        ctk.CTkLabel(form, text=label, anchor="w", width=210).grid(
            row=row, column=0, sticky="w", pady=12, padx=(0, 12))
        var = tk.StringVar(value=api.get(key, ""))
        entry = ctk.CTkEntry(form, textvariable=var, show="*" if masked else "", width=360)
        entry.grid(row=row, column=1, sticky="w", pady=12)
        self._vars[key] = var

        help_btn = ctk.CTkButton(form, text="?", width=34,
                                 command=lambda t=help_topic: HelpWindow(self, t))
        help_btn.grid(row=row, column=2, padx=(8, 0), pady=12)

        if masked:
            vis_var = tk.BooleanVar(value=False)
            def toggle(e=entry, v=vis_var):
                v.set(not v.get())
                e.configure(show="" if v.get() else "*")
            ctk.CTkButton(form, text="Ver", width=48, command=toggle).grid(
                row=row, column=3, padx=(4, 0), pady=12)

    def _save(self):
        api = self._app.config_data.setdefault("api", {})
        for k, v in self._vars.items():
            api[k] = v.get().strip()
        api["tts_voice"] = self._voice_var.get()
        save_config(self._app.config_data)
        messagebox.showinfo("Guardado", "Configuracion de API guardada correctamente.", parent=self)


# ════════════════════════════════════════════════════════════════
#  Pagina: Mi Tienda
# ════════════════════════════════════════════════════════════════

class StorePage(ctk.CTkFrame):
    def __init__(self, master: "App"):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._app = master
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._widgets: dict = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="Mi Tienda",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            self,
            text="Esta informacion le permite al bot responder preguntas sobre tu tienda.",
            text_color="gray60", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))
        scroll.columnconfigure(0, weight=1)

        store = self._app.config_data.get("store", {})

        simple = [
            ("Nombre de la tienda *", "name"),
            ("WhatsApp / Telefono  (ej: +51 940 143 234)", "whatsapp"),
            ("Ubicacion  (ej: Lima, Peru — solo tienda virtual)", "location"),
        ]
        r = 0
        for lbl, key in simple:
            ctk.CTkLabel(scroll, text=lbl, anchor="w").grid(row=r, column=0, sticky="w", pady=(10, 2))
            var = tk.StringVar(value=store.get(key, ""))
            ctk.CTkEntry(scroll, textvariable=var).grid(row=r + 1, column=0, sticky="ew")
            self._widgets[key] = var
            r += 2

        multi = [
            ("Descripcion de la tienda",
             "description",
             "Que vendes? Cual es tu propuesta de valor?\nEj: Vendemos suplementos importados de alta calidad para ninos y adultos."),
            ("Informacion adicional",
             "extra_info",
             "Politica de envios, horarios, garantia, redes sociales, etc."),
        ]
        for lbl, key, hint in multi:
            ctk.CTkLabel(scroll, text=lbl, anchor="w").grid(row=r, column=0, sticky="w", pady=(14, 2))
            box = ctk.CTkTextbox(scroll, height=90, wrap="word")
            val = store.get(key, "")
            if val:
                box.insert("end", val)
            box.grid(row=r + 1, column=0, sticky="ew")
            self._widgets[key] = box
            r += 2

        ctk.CTkButton(
            self, text="Guardar informacion", height=40,
            command=self._save,
        ).grid(row=3, column=0, sticky="w", padx=24, pady=(0, 16))

    def _save(self):
        store = self._app.config_data.setdefault("store", {})
        for k, w in self._widgets.items():
            if isinstance(w, tk.StringVar):
                store[k] = w.get().strip()
            else:
                store[k] = w.get("1.0", "end").strip()
        save_config(self._app.config_data)
        messagebox.showinfo("Guardado", "Informacion de tienda guardada.", parent=self)


# ════════════════════════════════════════════════════════════════
#  Pagina: Productos
# ════════════════════════════════════════════════════════════════

class ProductsPage(ctk.CTkFrame):
    def __init__(self, master: "App"):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._app = master
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._cards: list = []
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 4))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="Productos",
                     font=ctk.CTkFont(size=20, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hdr, text="+ Agregar producto", width=160,
                      command=self._add).grid(row=0, column=1)

        ctk.CTkLabel(
            self,
            text="Agrega aqui todos los productos que el bot debera conocer y vender.",
            text_color="gray60", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._scroll.columnconfigure(0, weight=1)

        self._refresh()

    def _refresh(self):
        for w in self._cards:
            w.destroy()
        self._cards.clear()

        products = self._app.config_data.get("products", [])
        if not products:
            lbl = ctk.CTkLabel(
                self._scroll,
                text="No hay productos. Haz clic en '+ Agregar producto' para empezar.",
                text_color="gray60",
            )
            lbl.grid(row=0, column=0, pady=50)
            self._cards.append(lbl)
            return

        for i, p in enumerate(products):
            card = self._card(i, p)
            card.grid(row=i, column=0, sticky="ew", pady=(0, 6))
            self._cards.append(card)

    def _card(self, idx: int, p: dict) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self._scroll)
        card.columnconfigure(0, weight=1)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=10)
        ctk.CTkLabel(info, text=p.get("name", "Sin nombre"),
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(anchor="w")
        detail = "  |  ".join(filter(None, [p.get("price", ""), p.get("for_whom", "")]))
        if detail:
            ctk.CTkLabel(info, text=detail, text_color="gray60", anchor="w").pack(anchor="w")
        desc = p.get("description", "")
        if desc:
            ctk.CTkLabel(info, text=desc[:80] + ("..." if len(desc) > 80 else ""),
                         text_color="gray50", anchor="w",
                         font=ctk.CTkFont(size=11)).pack(anchor="w")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=0, column=1, padx=10)
        ctk.CTkButton(btns, text="Editar", width=72,
                      command=lambda i=idx: self._edit(i)).pack(pady=2)
        ctk.CTkButton(btns, text="Eliminar", width=72, fg_color="#c0392b", hover_color="#922b21",
                      command=lambda i=idx: self._delete(i)).pack(pady=2)
        return card

    def _add(self):
        dlg = ProductDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self._app.config_data.setdefault("products", []).append(dlg.result)
            save_config(self._app.config_data)
            self._refresh()

    def _edit(self, idx: int):
        prods = self._app.config_data.get("products", [])
        dlg = ProductDialog(self, prods[idx])
        self.wait_window(dlg)
        if dlg.result:
            prods[idx] = dlg.result
            save_config(self._app.config_data)
            self._refresh()

    def _delete(self, idx: int):
        prods = self._app.config_data.get("products", [])
        if messagebox.askyesno("Eliminar", f"Eliminar '{prods[idx].get('name', 'producto')}'?", parent=self):
            prods.pop(idx)
            save_config(self._app.config_data)
            self._refresh()


# ════════════════════════════════════════════════════════════════
#  Pagina: Pitch
# ════════════════════════════════════════════════════════════════

class PitchPage(ctk.CTkFrame):
    def __init__(self, master: "App"):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._app = master
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._cards: list = []
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 4))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="Pitch de Venta",
                     font=ctk.CTkFont(size=20, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        ctk.CTkButton(btn_frame, text="+ Agregar segmento", width=160,
                      command=self._add).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_frame, text="Limpiar audios", width=130,
                      fg_color="gray40", command=self._clear_audio).pack(side="left")

        ctk.CTkLabel(
            self,
            text="Los segmentos se reproducen en orden en bucle. Cada uno se convierte en audio TTS.",
            text_color="gray60", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._scroll.columnconfigure(0, weight=1)

        self._refresh()

    def _refresh(self):
        for w in self._cards:
            w.destroy()
        self._cards.clear()

        segs = self._app.config_data.get("pitch_segments", [])
        if not segs:
            lbl = ctk.CTkLabel(
                self._scroll,
                text="No hay segmentos. Haz clic en '+ Agregar segmento' para empezar.",
                text_color="gray60",
            )
            lbl.grid(row=0, column=0, pady=50)
            self._cards.append(lbl)
            return

        for i, seg in enumerate(segs):
            card = self._card(i, seg, len(segs))
            card.grid(row=i, column=0, sticky="ew", pady=(0, 6))
            self._cards.append(card)

    def _card(self, idx: int, seg: dict, total: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self._scroll)
        card.columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=f"{idx+1}", width=30, anchor="center",
                     font=ctk.CTkFont(weight="bold"), text_color="gray55").grid(
            row=0, column=0, padx=(12, 4), pady=10)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", pady=10)
        ctk.CTkLabel(info, text=seg.get("id", ""), font=ctk.CTkFont(weight="bold"), anchor="w").pack(anchor="w")
        preview = seg.get("text", "")
        if len(preview) > 110:
            preview = preview[:110] + "..."
        ctk.CTkLabel(info, text=preview, text_color="gray55", anchor="w", wraplength=420).pack(anchor="w")

        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.grid(row=0, column=2, padx=4)
        if idx > 0:
            ctk.CTkButton(nav, text="^", width=34, height=28,
                          command=lambda i=idx: self._move(i, -1)).pack(pady=1)
        if idx < total - 1:
            ctk.CTkButton(nav, text="v", width=34, height=28,
                          command=lambda i=idx: self._move(i, 1)).pack(pady=1)

        act = ctk.CTkFrame(card, fg_color="transparent")
        act.grid(row=0, column=3, padx=(0, 10))
        ctk.CTkButton(act, text="Editar", width=72,
                      command=lambda i=idx: self._edit(i)).pack(pady=1)
        ctk.CTkButton(act, text="Eliminar", width=72, fg_color="#c0392b", hover_color="#922b21",
                      command=lambda i=idx: self._delete(i)).pack(pady=1)
        return card

    def _add(self):
        segs = self._app.config_data.get("pitch_segments", [])
        dlg = SegmentDialog(self, existing_ids=[s["id"] for s in segs])
        self.wait_window(dlg)
        if dlg.result:
            segs.append(dlg.result)
            self._app.config_data["pitch_segments"] = segs
            save_config(self._app.config_data)
            self._refresh()

    def _edit(self, idx: int):
        segs = self._app.config_data.get("pitch_segments", [])
        dlg = SegmentDialog(self, segment=segs[idx], existing_ids=[s["id"] for s in segs])
        self.wait_window(dlg)
        if dlg.result:
            self._rm_audio(segs[idx]["id"])
            segs[idx] = dlg.result
            self._rm_audio(dlg.result["id"])
            save_config(self._app.config_data)
            self._refresh()

    def _delete(self, idx: int):
        segs = self._app.config_data.get("pitch_segments", [])
        if messagebox.askyesno("Eliminar", f"Eliminar el segmento '{segs[idx].get('id', '')}'?", parent=self):
            self._rm_audio(segs[idx]["id"])
            segs.pop(idx)
            save_config(self._app.config_data)
            self._refresh()

    def _move(self, idx: int, d: int):
        segs = self._app.config_data.get("pitch_segments", [])
        new = idx + d
        if 0 <= new < len(segs):
            segs[idx], segs[new] = segs[new], segs[idx]
            save_config(self._app.config_data)
            self._refresh()

    def _rm_audio(self, seg_id: str):
        path = os.path.join("audio_cache", f"{seg_id}.mp3")
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def _clear_audio(self):
        if not messagebox.askyesno(
            "Limpiar audios del pitch",
            "Se eliminaran todos los archivos de audio generados.\n"
            "Se regeneraran automaticamente al iniciar el bot.\n\n"
            "Continuar?",
            parent=self,
        ):
            return
        cache = "audio_cache"
        removed = 0
        if os.path.exists(cache):
            for f in os.listdir(cache):
                if f.endswith(".mp3"):
                    try:
                        os.remove(os.path.join(cache, f))
                        removed += 1
                    except Exception:
                        pass
        messagebox.showinfo("Listo", f"Se eliminaron {removed} archivo(s) de audio.", parent=self)


# ════════════════════════════════════════════════════════════════
#  Pagina: Ajustes
# ════════════════════════════════════════════════════════════════

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master: "App"):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._app = master
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="Ajustes",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=24)
        form.columnconfigure(2, weight=1)

        settings = self._app.config_data.get("settings", {})

        # Modo prueba
        ctk.CTkLabel(form, text="Modo prueba", anchor="w", width=200).grid(
            row=0, column=0, sticky="w", pady=14, padx=(0, 16))
        self._test_var = tk.BooleanVar(value=settings.get("test_mode", False))
        ctk.CTkSwitch(form, variable=self._test_var, text="", onvalue=True, offvalue=False).grid(
            row=0, column=1, sticky="w", pady=14)
        ctk.CTkLabel(form, text="Sin live real — simula comentarios para probar el bot.",
                     text_color="gray60", anchor="w").grid(row=0, column=2, sticky="w", pady=14, padx=(12, 0))

        # Pausa entre segmentos
        ctk.CTkLabel(form, text="Pausa entre segmentos (s)", anchor="w", width=200).grid(
            row=1, column=0, sticky="w", pady=14, padx=(0, 16))
        self._pause_var = tk.StringVar(value=str(settings.get("pause_between_segments", 0.4)))
        ctk.CTkEntry(form, textvariable=self._pause_var, width=90).grid(
            row=1, column=1, sticky="w", pady=14)
        ctk.CTkLabel(form, text="Silencio entre cada bloque del pitch.",
                     text_color="gray60", anchor="w").grid(row=1, column=2, sticky="w", pady=14, padx=(12, 0))

        # Dispositivo de audio
        ctk.CTkLabel(form, text="Dispositivo de audio", anchor="w", width=200).grid(
            row=2, column=0, sticky="w", pady=14, padx=(0, 16))
        self._device_var = tk.StringVar(value=settings.get("audio_device", ""))
        ctk.CTkEntry(
            form, textvariable=self._device_var, width=320,
            placeholder_text="Vacio = predeterminado del sistema",
        ).grid(row=2, column=1, sticky="w", pady=14, columnspan=2)
        ctk.CTkButton(form, text="?", width=34,
                      command=lambda: HelpWindow(self, "audio_device")).grid(
            row=2, column=3, padx=(8, 0), pady=14)

        ctk.CTkButton(
            self, text="Guardar ajustes", height=40, command=self._save,
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(28, 0))

    def _save(self):
        settings = self._app.config_data.setdefault("settings", {})
        settings["test_mode"] = self._test_var.get()
        try:
            settings["pause_between_segments"] = float(self._pause_var.get())
        except ValueError:
            settings["pause_between_segments"] = 0.4
        settings["audio_device"] = self._device_var.get().strip()
        save_config(self._app.config_data)
        messagebox.showinfo("Guardado", "Ajustes guardados correctamente.", parent=self)


# ════════════════════════════════════════════════════════════════
#  Ventana principal
# ════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LiveSalesBot")
        self.geometry("1160x730")
        self.minsize(940, 620)

        self.config_data = load_config()
        self._bot: BotEngine | None = None
        self._log_buf: list[str] = []
        self._lock = threading.Lock()

        self._build()
        self._show("panel")
        self._poll()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(self, self._show, self._start_bot, self._stop_bot)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._pages: dict[str, ctk.CTkFrame] = {
            "panel":    PanelPage(self),
            "apis":     APIPage(self),
            "tienda":   StorePage(self),
            "productos": ProductsPage(self),
            "pitch":    PitchPage(self),
            "ajustes":  SettingsPage(self),
        }
        for page in self._pages.values():
            page.grid(row=0, column=1, sticky="nsew")
            page.grid_remove()

    def _show(self, name: str):
        for page in self._pages.values():
            page.grid_remove()
        self._pages[name].grid()
        self._sidebar.set_active(name)

    # ── log (thread-safe via buffer) ───────────────────────────

    def _log(self, msg: str):
        with self._lock:
            self._log_buf.append(msg)

    def _poll(self):
        with self._lock:
            msgs, self._log_buf = self._log_buf, []
        for msg in msgs:
            self._pages["panel"].append_log(msg)
        self.after(100, self._poll)

    def _set_status(self, running: bool):
        self.after(0, lambda: self._sidebar.set_running(running))

    # ── inicio / parada ────────────────────────────────────────

    def _start_bot(self):
        if self._bot and self._bot.running:
            messagebox.showinfo("Bot activo", "El bot ya esta en marcha.", parent=self)
            return
        if not self.config_data.get("api", {}).get("anthropic_api_key", ""):
            messagebox.showerror(
                "Falta API Key",
                "Debes configurar la Anthropic API Key antes de iniciar el bot.\n\n"
                "Ve a la seccion 'Configuracion API'.",
                parent=self,
            )
            self._show("apis")
            return
        self._bot = BotEngine(self.config_data, on_log=self._log, on_status=self._set_status)
        self._bot.start()
        self._log("Iniciando bot...")
        self._show("panel")

    def _stop_bot(self):
        if self._bot:
            self._bot.stop()
            self._bot = None
        self._set_status(False)


# ════════════════════════════════════════════════════════════════
#  Punto de entrada
# ════════════════════════════════════════════════════════════════

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
