import base64
import io
import json
import sys
import time
from pathlib import Path

try:
    import PIL.Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from google import genai
from google.genai import types

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent / "Mark-XXXV"

IMG_MAX_W = 640
IMG_MAX_H = 360
JPEG_Q = 55

SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Analyze images with technical precision and intelligence. "
    "Help the user in a way they can understand. "
    "Be concise, smart, and helpful. "
    "Respond in maximum 2 short sentences. Speed is priority."
)

def _get_api_key() -> str:
    sys.path.insert(0, str(get_base_dir()))
    from utils.api_keys import get_gemini_api_key
    return get_gemini_api_key()

def _to_jpeg(img_bytes: bytes) -> bytes:
    if not _PIL_OK:
        return img_bytes
    img = PIL.Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.thumbnail([IMG_MAX_W, IMG_MAX_H], PIL.Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_Q, optimize=False)
    return buf.getvalue()

def _capture_screenshot() -> bytes:
    import mss
    import mss.tools
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[1])
        png_bytes = mss.tools.to_png(shot.rgb, shot.size)
    return _to_jpeg(png_bytes)

def _capture_camera() -> bytes:
    import cv2
    camera_index = 0
    try:
        with open(get_base_dir() / "config" / "api_keys.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if "camera_index" in cfg:
            camera_index = int(cfg["camera_index"])
    except Exception:
        pass

    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Camera could not be opened: index {camera_index}")
    for _ in range(10):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        raise RuntimeError("Could not capture camera frame.")
    if _PIL_OK:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(rgb)
        img.thumbnail([IMG_MAX_W, IMG_MAX_H], PIL.Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_Q, optimize=False)
        return buf.getvalue()
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
    return buf.tobytes()

def screen_process(parameters: dict) -> str:
    user_text = (parameters or {}).get("text") or (parameters or {}).get("user_text", "")
    user_text = (user_text or "").strip()
    if not user_text:
        return "Please provide text describing what you want to know about the image."

    angle = (parameters or {}).get("angle", "screen").lower().strip()

    try:
        if angle == "camera":
            image_bytes = _capture_camera()
            mime_type = "image/jpeg"
        else:
            image_bytes = _capture_screenshot()
            mime_type = "image/jpeg"

        client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"parts": [{"inline_data": {"mime_type": mime_type, "data": b64}}, {"text": user_text}]}
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return response.text.strip() if response.text else "No response from vision model."

    except Exception as e:
        return f"Screen processing failed: {e}"
