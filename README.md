# Viral Clipper Pro

Aplicación web que descarga videos accesibles mediante yt-dlp, transcribe el audio con Whisper y propone momentos destacados con un modelo de OpenAI. Exporta clips verticales MP4.

## Requisitos
- Python 3.11+
- FFmpeg
- Una clave de API de OpenAI con facturación habilitada
- Acceso permitido al video que se procesa

## Ejecutar localmente
1. Instala FFmpeg.
2. `pip install -r requirements.txt`
3. Configura `OPENAI_API_KEY` como variable de entorno.
4. `uvicorn app:app --reload`
5. Abre `http://127.0.0.1:8000`.

## Publicar en Render
El archivo `render.yaml` configura un servicio Docker Starter y un disco persistente. Conecta el repositorio en Render, crea el Blueprint y añade `OPENAI_API_KEY` como variable secreta en el panel de Render. Revisa los precios actuales antes de confirmar el plan.

## Importante
- No subas `.env` ni compartas claves API.
- Esta versión es un prototipo: no tiene cuentas de usuario, cuotas, cola de trabajos ni aislamiento multiusuario.
- Los sitios pueden bloquear descargas o cambiar sus condiciones; algunos videos protegidos, privados o transmisiones en vivo no funcionarán.
- Usa solo contenido que tengas derecho a descargar y editar. Los costos de alojamiento y API corren por cuenta del operador.
