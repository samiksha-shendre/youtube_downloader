from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import yt_dlp
import subprocess

app = FastAPI()

@app.get("/download")
def download(url: str):
    # Step 1: Extract metadata (title, etc.)
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "video").replace(" ", "_")

    # Step 2: yt-dlp command to stream video
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "best",
        "-o", "-",
        url
    ]

    process = subprocess.Popen(
        ytdlp_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    def iterfile():
        for chunk in iter(lambda: process.stdout.read(1024), b""):
            yield chunk

    # Step 3: Return stream with filename in headers
    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"attachment; filename={title}.mp4"
        }
    )
