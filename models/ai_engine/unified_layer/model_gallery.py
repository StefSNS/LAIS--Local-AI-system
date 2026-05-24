"""
Model Gallery v1.0
Manages model configurations for fast switching between local SLMs and cloud LLMs.
Based on LocalAI gallery model pattern - YAML-based model profiles.
"""

import os
from pathlib import Path
from typing import Optional


MODEL_GALLERY_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "model_gallery"
MODEL_GALLERY_DIR.mkdir(parents=True, exist_ok=True)


class ModelProfile:
    """A single model configuration profile."""

    def __init__(
        self,
        name: str,
        backend: str = "local",
        model_id: str = "",
        description: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        context_length: int = 4096,
        threads: int = 4,
        batch_size: int = 512,
        gpu_layers: int = 0,
        mmap: bool = True,
        tags: list[str] = None,
        **kwargs,
    ):
        self.name = name
        self.backend = backend
        self.model_id = model_id
        self.description = description
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.context_length = context_length
        self.threads = threads
        self.batch_size = batch_size
        self.gpu_layers = gpu_layers
        self.mmap = mmap
        self.tags = tags or []
        self.kwargs = kwargs

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "backend": self.backend,
            "model_id": self.model_id,
            "description": self.description,
            "parameters": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "context_length": self.context_length,
                "threads": self.threads,
                "batch_size": self.batch_size,
                "gpu_layers": self.gpu_layers,
                "mmap": self.mmap,
            },
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelProfile":
        params = data.get("parameters", {})
        return cls(
            name=data["name"],
            backend=data.get("backend", "local"),
            model_id=data.get("model_id", ""),
            description=data.get("description", ""),
            max_tokens=params.get("max_tokens", 2048),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.9),
            context_length=params.get("context_length", 4096),
            threads=params.get("threads", 4),
            batch_size=params.get("batch_size", 512),
            gpu_layers=params.get("gpu_layers", 0),
            mmap=params.get("mmap", True),
            tags=data.get("tags", []),
        )


class ModelGallery:
    """
    Collection of model profiles for fast switching.
    Profiles stored as YAML files in knowledge/model_gallery/.
    """

    def __init__(self):
        self._profiles: dict[str, ModelProfile] = {}
        self._active_profile: Optional[str] = None
        self._load_gallery()
        if not self._profiles:
            self._create_defaults()

    def list_profiles(self) -> list[dict]:
        """List all available model profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def get_profile(self, name: str) -> Optional[ModelProfile]:
        """Get a specific profile by name."""
        return self._profiles.get(name)

    def get_active_profile(self) -> Optional[ModelProfile]:
        """Get the currently active profile."""
        if self._active_profile:
            return self._profiles.get(self._active_profile)
        return None

    def set_active(self, name: str) -> bool:
        """Switch to a different model profile."""
        if name in self._profiles:
            self._active_profile = name
            return True
        return False

    def add_profile(self, profile: ModelProfile) -> None:
        """Add a new model profile."""
        self._profiles[profile.name] = profile
        self._save_profile(profile)

    def remove_profile(self, name: str) -> bool:
        """Remove a model profile."""
        if name in self._profiles:
            del self._profiles[name]
            profile_path = MODEL_GALLERY_DIR / f"{name}.yaml"
            if profile_path.exists():
                profile_path.unlink()
            if self._active_profile == name:
                self._active_profile = None
            return True
        return False

    def search_by_tag(self, tag: str) -> list[ModelProfile]:
        """Find profiles matching a tag."""
        return [p for p in self._profiles.values() if tag in p.tags]

    def get_status(self) -> dict:
        """Get gallery status."""
        return {
            "total_profiles": len(self._profiles),
            "active_profile": self._active_profile,
            "profiles": list(self._profiles.keys()),
            "gallery_path": str(MODEL_GALLERY_DIR),
        }

    def _create_defaults(self) -> None:
        """Create default model profiles for known setups."""
        defaults = [
            ModelProfile(
                name="phi4-fast",
                backend="local",
                model_id="phi-4-mini",
                description="Fast local reasoning for routine tasks",
                max_tokens=2048,
                temperature=0.5,
                context_length=4096,
                threads=4,
                tags=["slm", "fast", "routine", "local"],
            ),
            ModelProfile(
                name="qwen-general",
                backend="local",
                model_id="qwen2.5-3b",
                description="Balanced local model for general tasks",
                max_tokens=4096,
                temperature=0.7,
                context_length=8192,
                threads=4,
                tags=["slm", "general", "local"],
            ),
            ModelProfile(
                name="gemini-complex",
                backend="cloud",
                model_id="gemini-2.5-flash",
                description="Cloud model for complex reasoning and analysis",
                max_tokens=8192,
                temperature=0.7,
                context_length=32768,
                tags=["llm", "complex", "cloud", "reasoning"],
            ),
            ModelProfile(
                name="gemini-creative",
                backend="cloud",
                model_id="gemini-2.5-flash",
                description="Cloud model with higher temperature for creative tasks",
                max_tokens=8192,
                temperature=1.0,
                top_p=0.95,
                context_length=32768,
                tags=["llm", "creative", "cloud"],
            ),
            ModelProfile(
                name="minimal",
                backend="local",
                model_id="phi-4-mini",
                description="Minimal resource usage - emergency mode",
                max_tokens=1024,
                temperature=0.3,
                context_length=2048,
                threads=2,
                batch_size=256,
                tags=["slm", "emergency", "minimal", "local"],
            ),
        ]

        for profile in defaults:
            self._profiles[profile.name] = profile
            self._save_profile(profile)

    def _load_gallery(self) -> None:
        """Load profiles from YAML files."""
        try:
            import yaml
            for yaml_file in MODEL_GALLERY_DIR.glob("*.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if data and "name" in data:
                        profile = ModelProfile.from_dict(data)
                        self._profiles[profile.name] = profile
                except Exception:
                    pass
        except ImportError:
            pass

    def _save_profile(self, profile: ModelProfile) -> None:
        """Save a profile as YAML."""
        try:
            import yaml
            profile_path = MODEL_GALLERY_DIR / f"{profile.name}.yaml"
            with open(profile_path, "w", encoding="utf-8") as f:
                yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)
        except ImportError:
            pass


_global_gallery: Optional[ModelGallery] = None


def get_model_gallery() -> ModelGallery:
    global _global_gallery
    if _global_gallery is None:
        _global_gallery = ModelGallery()
    return _global_gallery
