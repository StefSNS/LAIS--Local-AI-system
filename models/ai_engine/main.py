# ============================================================
#  AI Engine - Desktop AI interface
#  Project: AI Engine | Model: Qwen2.5-1.5B
# ============================================================
import sys
import os
import threading
import time
import importlib.util
import json

import customtkinter as ctk
import psutil

from llm_engine import chat
from plugin_manager import load_all, start_watcher, plugins

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")

def dynamic_import(module_name, filepath):
    sys.modules.pop(f"plugins.{module_name}", None)
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def get_plugin(name):
    path = os.path.join(PLUGINS_DIR, f"{name}.py")
    return dynamic_import(name, path)


class DesktopGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Engine")
        self.geometry("1200x800")
        self.configure(fg_color="#0d0d0d")
        
        load_all()
        
        self._build_layout()
        self._build_sidebar()
        self._build_chat_area()
        self._build_input()
        
        self._add_message("system", "Omnis AI ready. How can I help you?")
        self.update_system_stats()
    
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=200)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color="#171717", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(
            self.sidebar,
            text="OMNIS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e5e5e5"
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="+ New Chat",
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            height=40,
            corner_radius=8,
            command=self.new_chat
        )
        new_chat_btn.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        # Refine button
        refine_btn = ctk.CTkButton(
            self.sidebar,
            text="Refine",
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            height=40,
            corner_radius=8,
            command=self.run_refine
        )
        refine_btn.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        # Plugin dropdown menu
        self.plugin_label = ctk.CTkLabel(
            self.sidebar,
            text="Plugins",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8b8b8b"
        )
        self.plugin_label.grid(row=3, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Get available plugins
        self.available_plugins = [
            ("Search", "search:", "#00d4ff"),
            ("Code", "code:", "#89d185"),
            ("Define", "define:", "#f9826c"),
            ("Research", "research:", "#d2a8ff"),
            ("Launch", "launch:", "#79c0ff"),
        ]
        
        plugin_names = [name for name, _, _ in self.available_plugins]
        plugin_names.insert(0, "Select Plugin...")
        
        self.plugin_dropdown = ctk.CTkComboBox(
            self.sidebar,
            values=plugin_names,
            fg_color="#2a2a2a",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
            border_width=1,
            border_color="#2a2a2a",
            text_color="#e5e5e5",
            dropdown_fg_color="#2a2a2a",
            dropdown_text_color="#e5e5e5",
            dropdown_hover_color="#3a3a3a",
            height=36,
            corner_radius=6,
            command=self._on_plugin_selected
        )
        self.plugin_dropdown.grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.plugin_dropdown.set("Select Plugin...")
        
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="#0d0d0d", corner_radius=8)
        self.status_frame.grid(row=5, column=0, padx=15, pady=15, sticky="ew")
        
        self.ram_label = ctk.CTkLabel(
            self.status_frame,
            text="RAM: ...",
            font=ctk.CTkFont(size=11),
            text_color="#8b8b8b"
        )
        self.ram_label.pack(pady=5)
        
        self.cpu_label = ctk.CTkLabel(
            self.status_frame,
            text="CPU: ...",
            font=ctk.CTkFont(size=11),
            text_color="#8b8b8b"
        )
        self.cpu_label.pack(pady=5)
    
    def _build_chat_area(self):
        self.chat_container = ctk.CTkFrame(self, fg_color="#0d0d0d", corner_radius=0)
        self.chat_container.grid(row=0, column=1, sticky="nsew")
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)
        
        self.chat_scroll = ctk.CTkScrollableFrame(
            self.chat_container,
            fg_color="transparent",
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.chat_scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        
        self.messages_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self.messages_frame.pack(fill="both", expand=True)
    
    def _build_input(self):
        self.input_container = ctk.CTkFrame(self.chat_container, fg_color="#171717", corner_radius=12, height=80)
        self.input_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 20))
        self.input_container.grid_propagate(False)
        self.input_container.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkTextbox(
            self.input_container,
            fg_color="#0d0d0d",
            border_width=0,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            text_color="#e5e5e5",
            height=50,
            padx=15,
            pady=10,
            wrap="word"
        )
        self.input_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.input_entry.bind("<Return>", self._handle_enter)
        
        self.send_btn = ctk.CTkButton(
            self.input_container,
            text="",
            fg_color="#10a37f",
            hover_color="#0d8a66",
            width=40,
            height=40,
            corner_radius=8,
            command=self.send_message,
            image=self._create_send_icon()
        )
        self.send_btn.grid(row=0, column=1, padx=(5, 10), pady=10)
    
    def _create_send_icon(self):
        return None
    
    def _handle_enter(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"
    
    def new_chat(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
    
    def run_refine(self):
        """Run the daily refinement cycle."""
        self._add_message("system", "Starting refinement cycle...")
        threading.Thread(target=self._run_refine_thread, daemon=True).start()
    
    def _run_refine_thread(self):
        """Run refinement in background thread."""
        try:
            from plugins.self_refine import run_refinement
            
            def progress(msg):
                self.after(0, lambda: self._add_message("system", msg))
            
            result = run_refinement(progress_callback=progress)
            self.after(0, lambda: self._add_message("system", result))
        except Exception as e:
            self.after(0, lambda: self._add_message("error", f"Refinement failed: {str(e)}"))
    
    def quick_action(self, prefix, name):
        self.input_entry.delete("1.0", "end")
        self.input_entry.insert("1.0", f"{prefix} ")
        self.plugin_dropdown.set("Select Plugin...")
    
    def _on_plugin_selected(self, choice):
        """Handle plugin dropdown selection."""
        if choice == "Select Plugin...":
            return
        for name, prefix, color in self.available_plugins:
            if name == choice:
                self.quick_action(prefix, name)
                break
    
    def send_message(self):
        q = self.input_entry.get("1.0", "end").strip()
        if not q:
            return
        self.input_entry.delete("1.0", "end")
        self._add_message("user", q)
        threading.Thread(target=self._process_message, args=(q,), daemon=True).start()
    
    def _add_message(self, sender, text):
        msg_frame = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=(10, 5), anchor="w")
        
        avatar = ctk.CTkLabel(
            msg_frame,
            text="◯" if sender == "user" else "○",
            font=ctk.CTkFont(size=20),
            text_color="#10a37f" if sender == "lais" else "#e5e5e5",
            width=30
        )
        avatar.pack(side="left", padx=(0, 10))
        
        content_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True)
        
        sender_label = ctk.CTkLabel(
            content_frame,
            text="You" if sender == "user" else "Omnis",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e5e5e5" if sender == "user" else "#10a37f"
        )
        sender_label.pack(anchor="w")
        
        text_widget = ctk.CTkTextbox(
            content_frame,
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=14),
            text_color="#e5e5e5",
            wrap="word",
            state="normal",
            activate_scrollbars=True
        )
        text_widget.pack(fill="both", expand=True, pady=(5, 0))
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
        
        self.after(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        self.chat_scroll._parent_canvas.yview_moveto(1.0)
    
    def _process_message(self, q):
        self._show_typing()
        try:
            ql = q.strip().lower()
            r = "No response."
            
            if ql.startswith("search:"):
                ws = get_plugin("web_search")
                r = ws.search(q[7:].strip())
            elif ql.startswith("define:"):
                di = get_plugin("dictionary")
                r = di.define(q[7:].strip())
            elif ql.startswith("code:"):
                ad = get_plugin("agent_dispatcher")
                r = ad.dispatch(q[5:].strip(), "coder")
            elif ql.startswith("research:"):
                res = get_plugin("researcher")
                r = res.research_and_save(q[9:].strip())
            elif ql.startswith("launch:"):
                sc = get_plugin("system_control")
                r = sc.launch(q[7:].strip())
            else:
                try:
                    ir = get_plugin("intent_router")
                    label, handler = ir.route(ql)
                    if label and label != "chat":
                        r = handler(q, chat)
                    else:
                        r = chat(q)
                except Exception as e:
                    r = chat(q)
                     
        except Exception as e:
            r = f"Error: {str(e)}"
        
        self.after(0, self._hide_typing)
        self.after(0, lambda: self._add_message("lais", r))
    
    def _show_typing(self):
        self.typing_label = ctk.CTkLabel(
            self.messages_frame,
            text="Omnis is typing...",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#8b8b8b"
        )
        self.typing_label.pack(anchor="w", padx=40, pady=10)
        self.after(100, self._scroll_to_bottom)
    
    def _hide_typing(self):
        if hasattr(self, 'typing_label'):
            self.typing_label.destroy()
    
    def update_system_stats(self):
        try:
            ram = psutil.virtual_memory()
            free_mb = ram.available // (1024 * 1024)
            cpu = psutil.cpu_percent(interval=0.5)
            self.ram_label.configure(text=f"RAM: {free_mb} MB")
            self.cpu_label.configure(text=f"CPU: {cpu}%")
        except Exception as e:
            pass
        self.after(3000, self.update_system_stats)


if __name__ == "__main__":
    app = DesktopGUI()
    app.mainloop()
