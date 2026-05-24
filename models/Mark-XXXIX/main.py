import asyncio
import re
import threading
import json
import sys
import traceback
from pathlib import Path

import io
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

_stdout = sys.stdout
class _SafeStream:
    encoding = 'utf-8'
    def write(self, s):
        try: _stdout.write(s); _stdout.flush()
        except: _stdout.write(s.encode('utf-8', errors='replace').decode('utf-8', errors='replace')); _stdout.flush()
    def flush(self): _stdout.flush()
sys.stdout = _SafeStream()

import sounddevice as sd
from google import genai
from google.genai import types
from ui import JarvisUI

sys.path.insert(0, str(Path(__file__).parent))

try:
    from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt
except ImportError:
    def load_memory(): return {}
    def update_memory(m): pass
    def format_memory_for_prompt(m): return ""

_AI_ENGINE_PATH = Path(__file__).resolve().parent.parent / "ai_engine"
_LAIS_AVAILABLE = False
_LAIS_UNIFIED = None

if _AI_ENGINE_PATH.exists():
    sys.path.insert(0, str(_AI_ENGINE_PATH))
    sys.path.insert(0, str(_AI_ENGINE_PATH.parent))

    def _init_lais():
        global _LAIS_AVAILABLE, _LAIS_UNIFIED
        try:
            from unified_layer import load_unified_layer
            print("[JARVIS] Initializing LAIS unified layer...")
            _LAIS_UNIFIED = load_unified_layer("jarvis")
            _LAIS_AVAILABLE = True
            print("[JARVIS] LAIS unified layer connected OK")
            return True
        except Exception as e:
            print(f"[JARVIS] LAIS init: {e}")
            return False

    threading.Thread(target=_init_lais, daemon=True).start()

try:
    from actions.file_processor import file_processor
    from actions.flight_finder import flight_finder
    from actions.open_app import open_app
    from actions.weather_report import weather_action
    from actions.send_message import send_message
    from actions.reminder import reminder
    from actions.computer_settings import computer_settings
    from actions.screen_processor import screen_process
    from actions.youtube_video import youtube_video
    from actions.desktop import desktop_control
    from actions.browser_control import browser_control
    from actions.file_controller import file_controller
    from actions.code_helper import code_helper
    from actions.dev_agent import dev_agent
    from actions.web_search import web_search as web_search_action
    from actions.computer_control import computer_control
    from actions.game_updater import game_updater
except ImportError as e:
    print(f"[JARVIS] Some actions unavailable: {e}")
    def noop(*a, **k): return "Action not available"
    file_processor = flight_finder = open_app = weather_action = send_message = reminder = computer_settings = screen_process = youtube_video = desktop_control = browser_control = file_controller = code_helper = dev_agent = web_search_action = computer_control = game_updater = noop


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

def _get_api_key() -> str:
    if not API_CONFIG_PATH.exists():
        raise FileNotFoundError(f"API config not found at {API_CONFIG_PATH}")
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are JARVIS, an AI assistant. Be concise and use tools."

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()

TOOL_DECLARATIONS = [
    {"name": "open_app", "description": "Opens any application.", "parameters": {"type": "OBJECT", "properties": {"app_name": {"type": "STRING"}}, "required": ["app_name"]}},
    {"name": "web_search", "description": "Searches the web.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}},
    {"name": "weather_report", "description": "Weather report.", "parameters": {"type": "OBJECT", "properties": {"city": {"type": "STRING"}}, "required": ["city"]}},
    {"name": "send_message", "description": "Send message via WhatsApp/Telegram.", "parameters": {"type": "OBJECT", "properties": {"receiver": {"type": "STRING"}, "message_text": {"type": "STRING"}, "platform": {"type": "STRING"}}, "required": ["receiver", "message_text", "platform"]}},
    {"name": "reminder", "description": "Set a reminder.", "parameters": {"type": "OBJECT", "properties": {"date": {"type": "STRING"}, "time": {"type": "STRING"}, "message": {"type": "STRING"}}, "required": ["date", "time", "message"]}},
    {"name": "youtube_video", "description": "YouTube control.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "query": {"type": "STRING"}}, "required": []}},
    {"name": "screen_process", "description": "Capture and analyze screen.", "parameters": {"type": "OBJECT", "properties": {"angle": {"type": "STRING"}, "text": {"type": "STRING"}}, "required": ["text"]}},
    {"name": "computer_settings", "description": "Computer control.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": []}},
    {"name": "browser_control", "description": "Browser automation.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "url": {"type": "STRING"}, "query": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "file_controller", "description": "File management.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "path": {"type": "STRING"}, "destination": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "desktop_control", "description": "Desktop control.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "code_helper", "description": "Code assistance.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "description": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "dev_agent", "description": "Build projects.", "parameters": {"type": "OBJECT", "properties": {"description": {"type": "STRING"}}, "required": ["description"]}},
    {"name": "computer_control", "description": "Direct computer control.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "game_updater", "description": "Game updates.", "parameters": {"type": "OBJECT", "properties": {"platform": {"type": "STRING"}, "game_name": {"type": "STRING"}}, "required": []}},
    {"name": "flight_finder", "description": "Search flights.", "parameters": {"type": "OBJECT", "properties": {"origin": {"type": "STRING"}, "destination": {"type": "STRING"}, "date": {"type": "STRING"}}, "required": ["origin", "destination", "date"]}},
    {"name": "shutdown_jarvis", "description": "Shutdown JARVIS.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "save_memory", "description": "Save to memory.", "parameters": {"type": "OBJECT", "properties": {"category": {"type": "STRING"}, "key": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["category", "key", "value"]}},
    {"name": "vault_search", "description": "Search LAIS vault.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}, "max_results": {"type": "INTEGER"}}, "required": ["query"]}},
    {"name": "agent_message", "description": "Send to LAIS agent.", "parameters": {"type": "OBJECT", "properties": {"target_agent": {"type": "STRING"}, "message": {"type": "STRING"}}, "required": ["target_agent", "message"]}},
    {"name": "security_report", "description": "Security grid report.", "parameters": {"type": "OBJECT", "properties": {"sub_agent": {"type": "STRING"}}, "required": []}},
]

class JarvisLive:
    def __init__(self, ui: JarvisUI):
        self.ui = ui
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self.ui.on_text_command = self._on_text_command
        self._turn_done_event: asyncio.Event | None = None
        self.lais = None
        self.searcher = None
        self.agency = None

    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(turns={"parts": [{"text": text}]}, turn_complete=True),
            self._loop
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(turns={"parts": [{"text": text}]}, turn_complete=True),
            self._loop
        )

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime
        memory = load_memory()
        mem_str = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()
        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y - %I:%M %p")
        time_ctx = f"[CURRENT TIME] {time_str}"

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        print(f"[TOOL] {name}")
        self.ui.set_state("THINKING")

        if name == "save_memory":
            update_memory({args.get("category", "notes"): {args.get("key", ""): {"value": args.get("value", "")}}})
            return types.FunctionResponse(id=fc.id, name=name, response={"result": "ok"})

        loop = asyncio.get_event_loop()
        result = "Done."

        try:
            tool_map = {
                "open_app": lambda: open_app(parameters=args, response=None, player=self.ui),
                "weather_report": lambda: weather_action(parameters=args, player=self.ui),
                "browser_control": lambda: browser_control(parameters=args, player=self.ui),
                "file_controller": lambda: file_controller(parameters=args, player=self.ui),
                "send_message": lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None),
                "reminder": lambda: reminder(parameters=args, response=None, player=self.ui),
                "youtube_video": lambda: youtube_video(parameters=args, response=None, player=self.ui),
                "screen_process": lambda: screen_process(parameters=args, response=None, player=self.ui, session_memory=None),
                "computer_settings": lambda: computer_settings(parameters=args, response=None, player=self.ui),
                "desktop_control": lambda: desktop_control(parameters=args, player=self.ui),
                "code_helper": lambda: code_helper(parameters=args, player=self.ui, speak=self.speak),
                "dev_agent": lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak),
                "web_search": lambda: web_search_action(parameters=args, player=self.ui),
                "computer_control": lambda: computer_control(parameters=args, player=self.ui),
                "game_updater": lambda: game_updater(parameters=args, player=self.ui, speak=self.speak),
                "flight_finder": lambda: flight_finder(parameters=args, player=self.ui),
                "file_processor": lambda: file_processor(parameters=args, player=self.ui, speak=self.speak),
                "shutdown_jarvis": self._do_shutdown,
                "vault_search": lambda: self._vault_search(args),
                "agent_message": lambda: self._agent_message(args),
                "security_report": lambda: self._security_report(args),
            }

            if name in tool_map:
                r = await loop.run_in_executor(None, tool_map[name])
                result = r or "Done."
            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Tool error: {e}"
            traceback.print_exc()

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        return types.FunctionResponse(id=fc.id, name=name, response={"result": result})

    def _do_shutdown(self):
        self.ui.write_log("SYS: Shutdown.")
        self.speak("Goodbye, sir.")
        import time, os
        time.sleep(1)
        os._exit(0)

    def _vault_search(self, args):
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        try:
            sys.path.insert(0, str(_AI_ENGINE_PATH.parent))
            from unified_layer.unified_search import UnifiedSearch
            searcher = UnifiedSearch()
            results = searcher.search_all(query)
            if results:
                return "\n".join(str(r)[:200] for r in results[:max_results])
            return "No results."
        except Exception as e:
            return f"Vault error: {e}"

    def _agent_message(self, args):
        try:
            sys.path.insert(0, str(_AI_ENGINE_PATH.parent))
            from unified_layer.protocol_layer import load_protocol_layer
            proto = load_protocol_layer()
            if proto:
                resp = proto.send_a2a_message("jarvis", args.get("target_agent", ""), args.get("message", ""))
                return resp or "Sent."
            return "Protocol not available."
        except Exception as e:
            return f"Agent error: {e}"

    def _security_report(self, args):
        try:
            if self.agency:
                sub = args.get("sub_agent", "").strip().lower()
                if sub and sub in self.agency.sub_agents:
                    r = self.agency.sub_agents[sub].check()
                    return f"[{r.get('status','?').upper()}] {r.get('message','')}"
                return self.agency.report()
            return "Security Agency not initialized."
        except Exception as e:
            return f"Security error: {e}"

    async def _listen_audio(self):
        print("[MIC] Started")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                jarvis_speaking = self._is_speaking
            if not jarvis_speaking and not self.ui.muted:
                data = indata.tobytes()
                loop.call_soon_threadsafe(self.out_queue.put_nowait, {"data": data, "mime_type": "audio/pcm"})

        try:
            with sd.InputStream(samplerate=SEND_SAMPLE_RATE, channels=CHANNELS, dtype="int16", blocksize=CHUNK_SIZE, callback=callback):
                print("[MIC] Stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[MIC] Error: {e}")

    async def _receive_audio(self):
        print("[RECV] Started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():
                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"You: {full_in}")
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Jarvis: {full_out}")
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[CALL] {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(function_responses=fn_responses)
        except Exception as e:
            print(f"[RECV] Error: {e}")

    async def _play_audio(self):
        print("[PLAY] Started")
        stream = sd.RawOutputStream(samplerate=RECEIVE_SAMPLE_RATE, channels=CHANNELS, dtype="int16", blocksize=CHUNK_SIZE)
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[PLAY] Error: {e}")
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})

        while True:
            try:
                print("[CONNECT] Connecting...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session, asyncio.TaskGroup() as tg:
                    self.session = session
                    self._loop = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()

                    print("[OK] Connected.")
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: JARVIS online.")

                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                print(f"[WARN] {e}")
            self.set_speaking(False)
            self.ui.set_state("THINKING")
            print("[RECON] Reconnecting in 3s...")
            await asyncio.sleep(3)

def main():
    face_path = Path(__file__).parent / "face.png"
    ui = JarvisUI(str(face_path) if face_path.exists() else None)

    def runner():
        ui.wait_for_api_key()
        jarvis = JarvisLive(ui)

        try:
            from agency import SecurityAgency
            jarvis.agency = SecurityAgency()
            jarvis.agency.start_monitoring()
            print("[OK] Security Agency online")
            ui.write_log("SYS: Security Agency active.")
        except Exception as e:
            print(f"[WARN] Security init: {e}")

        if _LAIS_AVAILABLE:
            jarvis.lais = _LAIS_UNIFIED
            print("[OK] LAIS connected")
            ui.write_log("SYS: LAIS connected.")

        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n[SHUTDOWN]")

    threading.Thread(target=runner, daemon=True).start()
    sys.exit(ui.app.exec())

if __name__ == "__main__":
    main()
