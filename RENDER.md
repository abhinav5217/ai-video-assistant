# AI Video Assistant — Render deployment

## Render settings

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

Set these environment variables in Render:

- `APP_USERNAME`
- `APP_PASSWORD`
- `OPENAI_API_KEY`

FFmpeg is installed from `packages.txt`.

## YouTube downloads

The application no longer depends on BgUtils or Deno. YouTube URLs are handled directly by yt-dlp, and FFmpeg normalizes the downloaded audio before transcription.

Some YouTube videos can still be unavailable when YouTube requires an authentication/PO-token flow that the selected yt-dlp client cannot satisfy. That is an upstream YouTube/yt-dlp limitation, not a missing BgUtils dependency.

## Local file uploads

Uploaded audio/video files continue to use the same FFmpeg/PyDub normalization and chunking pipeline.
