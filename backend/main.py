from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import uuid
import shutil
import threading
import time

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://YOUR-frontend.vercel.app", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Cleanup function to delete files after some time
def cleanup_file(path, delay=120):
    def _delete():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=_delete, daemon=True).start()

def download_video(url, download_id):
    output_template = f'{DOWNLOAD_DIR}/{download_id}.%(ext)s'
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        # Force .mp4 extension if merge happened
        if not filename.endswith(".mp4"):
            filename = f"{DOWNLOAD_DIR}/{download_id}.mp4"

        return filename

@app.post("/download")
async def download(request: Request):
    data = await request.json()
    urls = data.get("urls", [])
    if not urls:
        return JSONResponse({"error": "No URLs provided"}, status_code=400)

    file_paths = []
    for url in urls:
        download_id = str(uuid.uuid4())
        file_path = download_video(url, download_id)
        file_paths.append(file_path)

    # If only one file, return it directly
    if len(file_paths) == 1:
        file_path = file_paths[0]
        cleanup_file(file_path)  # delete later
        return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))

    # If multiple files, zip them together
    zip_name = f"{DOWNLOAD_DIR}/videos_{uuid.uuid4()}.zip"
    with shutil.ZipFile(zip_name, 'w') as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))
            cleanup_file(file_path)  # schedule cleanup for individual files
    cleanup_file(zip_name)  # cleanup zip too

    return FileResponse(zip_name, media_type="application/zip", filename="videos.zip")
