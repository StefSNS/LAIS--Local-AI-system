"""
Docling Document Ingestion - Parse PDFs, Word docs, PPTX, Excel, HTML into clean text.
Feeds extracted content into the knowledge vault and memory system.

RAM footprint: ~300MB (when actively processing)
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

VAULT_PATH = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge")
INGESTION_OUTPUT = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\ingested")
INGESTION_OUTPUT.mkdir(parents=True, exist_ok=True)


class DocIngester:
    """
    Document ingestion pipeline using Docling.
    Supports: PDF, DOCX, PPTX, XLSX, HTML, images with OCR
    Extracts text, tables, metadata, and structures content.
    """

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path or VAULT_PATH
        self.output_path = INGESTION_OUTPUT
        self._docling_ready = False

        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            self._docling_ready = True
            print("[DocIngester] Docling loaded successfully")
        except Exception as e:
            print(f"[DocIngester] Docling unavailable ({e}), limited functionality")
            self.converter = None

    def ingest_file(self, file_path: Path, save_to_vault: bool = True) -> Dict[str, Any]:
        """
        Ingest a single document.
        Returns extracted text, metadata, and optionally saves to vault.
        """
        if not self._docling_ready or self.converter is None:
            return self._fallback_ingest(file_path)

        start = time.time()
        file_path = Path(file_path)

        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            result = self.converter.convert(str(file_path))
            text = result.document.export_to_markdown()

            metadata = {
                "source_file": str(file_path.name),
                "source_path": str(file_path),
                "file_size_kb": round(file_path.stat().st_size / 1024, 1),
                "file_type": file_path.suffix.lower(),
                "ingested_at": datetime.now().isoformat(),
                "processing_time_s": round(time.time() - start, 2),
                "text_length": len(text),
            }

            if save_to_vault:
                self._save_to_vault(file_path.stem, text, metadata)

            return {
                "text": text[:5000],
                "text_full_length": len(text),
                "metadata": metadata,
                "success": True,
            }

        except Exception as e:
            return {
                "error": str(e),
                "source_file": str(file_path.name),
                "success": False,
                "processing_time_s": round(time.time() - start, 2),
            }

    def ingest_directory(self, dir_path: Path, pattern: str = "*") -> List[Dict[str, Any]]:
        """Ingest all supported documents in a directory."""
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return [{"error": f"Directory not found: {dir_path}"}]

        supported_exts = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".txt", ".md"}
        results = []

        for fpath in dir_path.glob(pattern):
            if fpath.is_file() and fpath.suffix.lower() in supported_exts:
                result = self.ingest_file(fpath)
                results.append(result)

        return results

    def _fallback_ingest(self, file_path: Path) -> Dict[str, Any]:
        """Fallback text extraction when Docling is unavailable."""
        file_path = Path(file_path)

        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        ext = file_path.suffix.lower()
        text = ""

        try:
            if ext in (".txt", ".md", ".json", ".py", ".js", ".ts", ".html", ".htm", ".csv"):
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            else:
                return {
                    "error": f"Unsupported format without Docling: {ext}",
                    "source_file": file_path.name,
                    "success": False,
                }

            metadata = {
                "source_file": file_path.name,
                "source_path": str(file_path),
                "file_size_kb": round(file_path.stat().st_size / 1024, 1),
                "file_type": ext,
                "ingested_at": datetime.now().isoformat(),
                "extraction_method": "fallback_read",
                "text_length": len(text),
            }

            return {
                "text": text[:5000],
                "text_full_length": len(text),
                "metadata": metadata,
                "success": True,
            }

        except Exception as e:
            return {"error": str(e), "source_file": file_path.name, "success": False}

    def _save_to_vault(self, doc_name: str, text: str, metadata: Dict[str, Any]):
        """Save ingested document to the knowledge vault."""
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in doc_name)
        output_file = self.output_path / f"{safe_name}.md"

        content = f"""# {doc_name}

## Source
- **File**: {metadata.get('source_file', 'unknown')}
- **Type**: {metadata.get('file_type', 'unknown')}
- **Size**: {metadata.get('file_size_kb', 0)}KB
- **Ingested**: {metadata.get('ingested_at', 'unknown')}
- **Processing Time**: {metadata.get('processing_time_s', 0)}s

---

{text}
"""
        output_file.write_text(content, encoding="utf-8")

    def get_ingestion_log(self) -> List[Dict[str, Any]]:
        """Get a list of all ingested documents."""
        log = []
        for fpath in sorted(self.output_path.glob("*.md")):
            stat = fpath.stat()
            log.append({
                "file": fpath.name,
                "path": str(fpath),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return log

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        ingested = self.get_ingestion_log()
        return {
            "total_ingested": len(ingested),
            "total_size_mb": round(sum(d["size_kb"] for d in ingested) / 1024, 2),
            "docling_ready": self._docling_ready,
            "recent": ingested[-5:] if ingested else [],
        }


def load_doc_ingester(vault_path=None) -> DocIngester:
    """Factory function."""
    return DocIngester(vault_path)


if __name__ == "__main__":
    print("=== Docling Document Ingestion ===")
    ingester = load_doc_ingester()

    stats = ingester.get_stats()
    print(f"Docling ready: {stats['docling_ready']}")
    print(f"Total ingested: {stats['total_ingested']}")
    print(f"Total size: {stats['total_size_mb']}MB")

    if stats["recent"]:
        print("\nRecent ingestions:")
        for d in stats["recent"]:
            print(f"  - {d['file']} ({d['size_kb']}KB)")

    # Test fallback ingestion on a markdown file
    test_file = VAULT_PATH / "artificial_intelligence.md"
    if test_file.exists():
        print(f"\n=== Testing fallback ingest: {test_file.name} ===")
        result = ingester.ingest_file(test_file)
        if result.get("success"):
            print(f"  Extracted {result['text_full_length']} chars in {result['metadata'].get('processing_time_s', 0)}s")
        else:
            print(f"  Error: {result.get('error')}")
