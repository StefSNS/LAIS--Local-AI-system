"""
Browsegrab Plugin - Lightweight browser automation for LAIS
Uses browsegrab (Playwright + accessibility tree + MarkGrab) for token-efficient browser control.
Optimized for 3GB RAM: headless Chromium, no GPU, minimal context.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from browsegrab import BrowseSession
    BROWSEGRAB_AVAILABLE = True
except ImportError:
    BROWSEGRAB_AVAILABLE = False
    print("[WARN] browsegrab not installed. Run: pip install browsegrab")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class BrowserAgent:
    """Lightweight browser agent using browsegrab for automation."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.session: Optional[BrowseSession] = None
        self._is_running = False
    
    async def start(self) -> bool:
        """Initialize browsegrab session."""
        if not BROWSEGRAB_AVAILABLE:
            print("[Browser] browsegrab not available")
            return False
        
        try:
            os.environ["BROWSEGRAB_BROWSER_HEADLESS"] = str(self.headless).lower()
            os.environ["BROWSEGRAB_BROWSER_TIMEOUT_MS"] = "30000"
            os.environ["BROWSEGRAB_AGENT_MAX_STEPS"] = "15"
            os.environ["BROWSEGRAB_AGENT_ENABLE_CACHE"] = "true"
            
            self.session = BrowseSession()
            await self.session.__aenter__()
            self._is_running = True
            print("[Browser] browsegrab session started")
            return True
        except Exception as e:
            print(f"[Browser] Failed to start: {e}")
            return False
    
    async def stop(self):
        """Close browsegrab session."""
        if self.session and self._is_running:
            try:
                await self.session.__aexit__(None, None, None)
                self._is_running = False
                print("[Browser] Session closed")
            except Exception as e:
                print(f"[Browser] Error closing session: {e}")
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL and return accessibility tree snapshot."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            await self.session.navigate(url)
            snap = await self.session.snapshot()
            return {
                "url": snap.url if hasattr(snap, "url") else url,
                "title": snap.title if hasattr(snap, "title") else "",
                "tree": snap.tree_text if hasattr(snap, "tree_text") else str(snap),
                "interactive_elements": self._count_interactive(snap),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def click(self, ref: str) -> Dict[str, Any]:
        """Click element by ref ID (e1, e2, etc)."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            result = await self.session.click(ref)
            return {
                "success": True,
                "url": result.url if hasattr(result, "url") else "",
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def type_text(self, ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        """Type text into element by ref ID."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            await self.session.type(ref, text, submit=submit)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_content(self) -> Dict[str, Any]:
        """Extract page content as markdown (via MarkGrab)."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            content = await self.session.extract_content()
            return {
                "success": True,
                "content": content if isinstance(content, str) else str(content),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def scroll(self, direction: str = "down") -> Dict[str, Any]:
        """Scroll page."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            await self.session.scroll(direction)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def go_back(self) -> Dict[str, Any]:
        """Go back in browser history."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            await self.session.go_back()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def snapshot(self) -> Dict[str, Any]:
        """Get current accessibility tree snapshot."""
        if not self.session:
            return {"error": "Session not started"}
        
        try:
            snap = await self.session.snapshot()
            return {
                "tree": snap.tree_text if hasattr(snap, "tree_text") else str(snap),
                "interactive_elements": self._count_interactive(snap),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _count_interactive(self, snap) -> int:
        """Count interactive elements in snapshot."""
        if hasattr(snap, "tree_text"):
            text = snap.tree_text
            return text.count("[ref=")
        return 0
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._is_running,
            "headless": self.headless,
            "available": BROWSEGRAB_AVAILABLE,
        }


# Singleton
_browser_agent: Optional[BrowserAgent] = None
_loop: Optional[asyncio.AbstractEventLoop] = None


def get_browser_agent() -> BrowserAgent:
    """Get or create the singleton browser agent."""
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent(headless=True)
    return _browser_agent


def run_browser_async(coro):
    """Run an async browser operation from sync code."""
    global _loop
    
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    
    return _loop.run_until_complete(coro)


# ── Plugin interface for LAIS ────────────────────────────────────────────────

def get_plugin_info():
    return {
        "name": "browser_agent",
        "version": "1.0",
        "description": "Lightweight browser automation via browsegrab",
        "author": "LAIS Team",
    }


def execute(command: str, **kwargs) -> Dict[str, Any]:
    """
    Execute browser command from LAIS plugin system.
    
    Commands:
        navigate <url>     - Navigate to URL
        click <ref>        - Click element by ref ID
        type <ref> <text>  - Type text into element
        extract            - Extract page content as markdown
        scroll <direction> - Scroll page (up/down)
        back               - Go back
        snapshot           - Get accessibility tree
        status             - Get browser status
    """
    agent = get_browser_agent()
    parts = command.lower().split()
    
    if not parts:
        return {"error": "No command provided"}
    
    cmd = parts[0]
    
    if cmd == "navigate":
        if len(parts) < 2:
            return {"error": "URL required"}
        return run_browser_async(agent.navigate(parts[1]))
    
    elif cmd == "click":
        if len(parts) < 2:
            return {"error": "Element ref required"}
        return run_browser_async(agent.click(parts[1]))
    
    elif cmd == "type":
        if len(parts) < 3:
            return {"error": "Element ref and text required"}
        return run_browser_async(agent.type_text(parts[1], " ".join(parts[2:])))
    
    elif cmd == "extract":
        return run_browser_async(agent.extract_content())
    
    elif cmd == "scroll":
        direction = parts[1] if len(parts) > 1 else "down"
        return run_browser_async(agent.scroll(direction))
    
    elif cmd == "back":
        return run_browser_async(agent.go_back())
    
    elif cmd == "snapshot":
        return run_browser_async(agent.snapshot())
    
    elif cmd == "status":
        return agent.get_status()
    
    elif cmd == "start":
        return run_browser_async(agent.start())
    
    elif cmd == "stop":
        return run_browser_async(agent.stop())
    
    else:
        return {"error": f"Unknown command: {cmd}"}
