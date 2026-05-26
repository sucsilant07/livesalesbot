@echo off
echo ============================================
echo   LiveSalesBot - Instalando dependencias
echo ============================================
echo.

pip install -r requirements.txt

echo.
echo ============================================
echo   Instalacion completada!
echo ============================================
echo.
echo PROXIMOS PASOS:
echo.
echo 1. Ejecuta el bot con:
echo      python main.py
echo.
echo 2. Se abrira la interfaz grafica.
echo    Configura todo desde ahi:
echo.
echo    > Configuracion API
echo      - Tu @ de TikTok
echo      - Session ID de TikTok  (usa Cookie-Editor en Chrome)
echo      - Anthropic API Key     (console.anthropic.com)
echo      - Voz del bot (TTS)
echo.
echo    > Mi Tienda
echo      - Nombre, WhatsApp, ubicacion, descripcion
echo.
echo    > Productos
echo      - Agrega todos los productos que el bot vendera
echo.
echo    > Pitch
echo      - Crea los segmentos de audio que se reproduciran en bucle
echo.
echo    > Ajustes
echo      - Modo prueba, pausa entre segmentos, dispositivo de audio
echo.
echo 3. Haz clic en "Iniciar Bot" para arrancar.
echo.
echo NOTA: Para transmitir el audio con OBS instala VB-Audio Cable
echo y configura el dispositivo de audio en la seccion Ajustes.
echo.
pause
