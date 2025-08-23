from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import uuid
import shutil

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url, download_id):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/{download_id}.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not filename.endswith(".mp4"):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
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

    # If single file → return directly
    if len(file_paths) == 1:
        return FileResponse(file_paths[0], media_type="video/mp4", filename=os.path.basename(file_paths[0]))

    # If multiple files → zip them
    zip_name = f"{DOWNLOAD_DIR}/videos_{uuid.uuid4()}.zip"
    shutil.make_archive(zip_name.replace(".zip", ""), 'zip', DOWNLOAD_DIR)
    return FileResponse(zip_name, media_type="application/zip", filename="videos.zip")
