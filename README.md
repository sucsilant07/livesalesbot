<h1 align="center">
  <br>
  LiveSalesBot
  <br>
</h1>

<p align="center">
  <strong>Bot de ventas con IA para TikTok Live — automatiza respuestas, reproduce pitches y cierra más ventas en tiempo real.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Claude-Haiku%204.5-7C3AED?style=flat-square&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/TikTok%20Live-API-010101?style=flat-square&logo=tiktok&logoColor=white"/>
  <img src="https://img.shields.io/badge/CustomTkinter-GUI-1F6AA5?style=flat-square"/>
  <img src="https://img.shields.io/badge/Edge%20TTS-Voz-0078D4?style=flat-square&logo=microsoft&logoColor=white"/>
</p>

---

## ¿Qué es LiveSalesBot?

LiveSalesBot es una herramienta de automatización para vendedores en **TikTok Live**. Mientras transmites en vivo, el bot:

1. **Monitorea comentarios** de tu audiencia en tiempo real.
2. **Detecta preguntas sobre productos** usando inteligencia artificial.
3. **Genera respuestas contextuales** basadas en tu catálogo de productos.
4. **Habla en voz alta** a través de los parlantes, como si fuera un asistente de ventas.
5. **Reproduce pitches automáticos** en bucle mientras no hay preguntas, manteniendo el live activo.

Todo esto sin que tengas que escribir una sola palabra durante el live.

---

## Demo del flujo

```
Espectador comenta: "¿El Omega 3 sirve para personas mayores?"
         │
         ▼
   [Claude Haiku]  →  ¿Es pregunta sobre producto? → Sí
         │
         ▼
   [Claude Haiku]  →  Genera respuesta usando el catálogo
         │             "¡Claro que sí! Nuestro Omega 3 importado de Noruega
         │              es perfecto para adultos mayores, ayuda a la salud
         │              cardiovascular. Precio: S/ 89. Escríbenos al WhatsApp."
         ▼
   [Edge TTS]      →  Convierte la respuesta a audio MP3
         │
         ▼
   [Pygame]        →  Reproduce el audio en los parlantes del PC en vivo
```

---

## Tecnologías utilizadas

| Tecnología | Rol en el proyecto |
|---|---|
| **Python 3.10+** | Lenguaje principal, asyncio, threading |
| **Claude API (Anthropic)** | Clasificación de preguntas y generación de respuestas |
| **TikTokLive SDK** | Conexión a la API no oficial de TikTok Live |
| **Microsoft Edge TTS** | Síntesis de voz (Text-to-Speech) en español |
| **Pygame** | Reproducción de archivos de audio MP3 |
| **CustomTkinter** | Interfaz gráfica moderna con tema oscuro |
| **asyncio + threading** | Concurrencia: TikTok y audio corren en paralelo |
| **python-dotenv** | Gestión de variables de entorno y secretos |
| **httpx** | Cliente HTTP moderno para comunicaciones |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        gui.py (CustomTkinter)               │
│  ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌───────┐ │
│  │   API    │ │Tienda  │ │Productos │ │ Pitch  │ │Ajustes│ │
│  └──────────┘ └────────┘ └──────────┘ └────────┘ └───────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ config_manager.py (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      bot_engine.py                          │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ TikTok Live │───▶│  Claude API  │───▶│   Edge TTS    │  │
│  │  (thread)   │    │  (asyncio)   │    │   (asyncio)   │  │
│  └─────────────┘    └──────────────┘    └───────┬───────┘  │
│                                                 │           │
│                          ┌──────────────────────▼────────┐  │
│                          │      Pygame Audio Player      │  │
│                          │   pitch_loop + response_queue │  │
│                          └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Decisiones de diseño clave:**
- **Thread separado para TikTok:** El SDK de TikTokLive es bloqueante; correrlo en un hilo propio evita que congele la GUI.
- **Cola de respuestas (`queue.Queue`):** Desacopla la generación de audio de su reproducción, permitiendo procesar múltiples comentarios sin interrumpir el pitch en curso.
- **Caché de audio:** Los segmentos de pitch se pre-generan en MP3 al iniciar el bot. Solo las respuestas dinámicas se generan en tiempo real.
- **Claude Haiku:** Se eligió el modelo más rápido y económico de Anthropic, ideal para clasificaciones de 1 token y respuestas cortas de ventas.

---

## Características

- **Interfaz gráfica completa** — No requiere tocar código. Configura todo desde la GUI.
- **Catálogo de productos** — CRUD visual para gestionar nombre, precio, descripción y beneficios de cada producto.
- **Segmentos de pitch** — Define y reordena los fragmentos que el bot repetirá en bucle durante el live.
- **Respuestas con IA** — Claude lee tu catálogo y responde preguntas con contexto real de tu tienda.
- **Síntesis de voz** — Compatible con más de 300 voces en español de distintos países (Perú, México, España, etc.).
- **Modo prueba** — Simula comentarios sin necesidad de estar en un live real. Ideal para testear.
- **Logs en tiempo real** — Panel de control que muestra cada evento: comentarios, respuestas, reproducción de audio.
- **Pausa configurable** — Ajusta el tiempo entre segmentos de pitch según el ritmo de tu live.
- **Selección de dispositivo de audio** — Elige en qué dispositivo de audio se escucha el bot.

---

## Instalación

### Requisitos previos

- Python 3.10 o superior
- Una cuenta de TikTok con acceso a transmisiones en vivo
- API Key de [Anthropic](https://console.anthropic.com) (requiere método de pago)

### Instalación rápida (Windows)

```bash
# 1. Clona el repositorio
git clone https://github.com/sucsilant07/livesalesbot.git
cd livesalesbot

# 2. Ejecuta el script de instalación
setup.bat
```

### Instalación manual

```bash
# 1. Clona el repositorio
git clone https://github.com/sucsilant07/livesalesbot.git
cd livesalesbot

# 2. Crea y activa un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Copia el archivo de entorno
copy .env.example .env
```

---

## Configuración

### Variables de entorno (`.env`)

Abre el archivo `.env` y completa tus credenciales:

```env
# Clave de API de Anthropic (console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx

# Usuario de TikTok (con @)
TIKTOK_USERNAME=@tu_usuario_tiktok

# Session ID de TikTok
TIKTOK_SESSION_ID=tu_session_id_aqui
```

#### ¿Cómo obtener el `TIKTOK_SESSION_ID`?

1. Instala la extensión [Cookie-Editor](https://cookie-editor.com/) en Chrome.
2. Ve a [tiktok.com](https://tiktok.com) e inicia sesión.
3. Abre Cookie-Editor y busca la cookie llamada `sessionid`.
4. Copia el valor y pégalo en tu `.env`.

> **Nota:** El `sessionid` puede caducar. Si el bot no se conecta, renuévalo.

### Configuración desde la GUI

Ejecuta el bot y configura todo visualmente:

```bash
python main.py
```

La GUI tiene seis secciones:

| Sección | Qué configuras |
|---|---|
| **Configuración API** | TikTok username, session ID, Anthropic API Key, voz TTS |
| **Mi Tienda** | Nombre, descripción, WhatsApp, ubicación, info adicional |
| **Productos** | Catálogo completo con nombre, precio, descripción y beneficios |
| **Pitch** | Segmentos de texto que el bot leerá en bucle durante el live |
| **Ajustes** | Modo prueba, pausa entre segmentos, dispositivo de audio |
| **Panel Principal** | Logs en tiempo real del bot en ejecución |

---

## Uso

```bash
python main.py
```

1. Abre la GUI y configura tu tienda, productos y pitch.
2. Activa **Modo Prueba** si quieres probar sin estar en un live real.
3. Haz clic en **"Iniciar Bot"**.
4. El bot se conectará a tu TikTok Live y comenzará a funcionar.
5. Observa los logs en el **Panel Principal** para ver comentarios y respuestas.
6. Haz clic en **"Detener Bot"** cuando termines.

---

## Estructura del proyecto

```
livesalesbot/
├── main.py                  # Punto de entrada
├── gui.py                   # Interfaz gráfica (CustomTkinter)
├── bot_engine.py            # Motor del bot (TikTok + Claude + TTS)
├── config_manager.py        # Persistencia de configuración en JSON
├── test_tiktok.py           # Script de diagnóstico de conexión TikTok
├── debug_html.py            # Script de debug para room_id
├── requirements.txt         # Dependencias
├── setup.bat                # Instalador rápido para Windows
├── .env.example             # Plantilla de variables de entorno
└── .gitignore
```

---

## Costos estimados de API

| Operación | Modelo | Costo aproximado |
|---|---|---|
| Clasificar un comentario | Claude Haiku 4.5 | ~$0.000001 |
| Generar una respuesta | Claude Haiku 4.5 | ~$0.00005 |
| Síntesis de voz (TTS) | Microsoft Edge TTS | **Gratuito** |

Para un live de 1 hora con ~200 preguntas, el costo de API es menor a **$0.02 USD**.

---

## Solución de problemas

**El bot no se conecta a TikTok Live**
- Verifica que tu `sessionid` sea válido y no haya caducado.
- Usa `python test_tiktok.py` para diagnosticar la conexión.
- Asegúrate de que la cuenta de TikTok pueda transmitir en vivo.

**No se escucha audio**
- Verifica que pygame esté instalado: `pip install pygame`.
- Revisa la sección **Ajustes** → **Dispositivo de audio** en la GUI.

**Error con la API de Anthropic**
- Confirma que tu API Key sea válida en [console.anthropic.com](https://console.anthropic.com).
- Verifica que tengas saldo disponible en tu cuenta.

---

## Contribuir

1. Haz fork del repositorio.
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`.
3. Realiza tus cambios y haz commit: `git commit -m "feat: nueva funcionalidad"`.
4. Haz push: `git push origin feature/nueva-funcionalidad`.
5. Abre un Pull Request.

---

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

<p align="center">
  Desarrollado con Python, Claude API y TikTokLive SDK
</p>
