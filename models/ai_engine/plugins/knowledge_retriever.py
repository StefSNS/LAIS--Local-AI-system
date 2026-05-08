import os
import json
import time

_cache = {"files": None, "timestamp": 0}
CACHE_TTL = 30

def scan_knowledge():
    now = time.time()
    if _cache["files"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["files"]
    
    try:
        files = os.listdir('knowledge')
        result = [f for f in files if f.endswith('.md')]
        _cache["files"] = result
        _cache["timestamp"] = now
        return result
    except Exception as e:
        return []
 
def search_knowledge(query):
    results = []
    query_words = query.lower().split()
    
    for filename in scan_knowledge():
        filepath = f"knowledge/{filename}"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content_lower = content.lower()
            score = sum(1 for word in query_words if word in content_lower)
            
            if score > 0:
                preview = content[:300]
                results.append({
                    'file': filename,
                    'score': score,
                    'preview': preview
                })
        except Exception as e:
            continue
     
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def get_context(query, max_files=3):
    matches = search_knowledge(query)
    
    if not matches:
        return ""
    
    context_parts = []
    for match in matches[:max_files]:
        filepath = f"knowledge/{match['file']}"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            context_parts.append(f"[From {match['file']}]:\n{content[:500]}")
        except Exception as e:
            continue
    
    return "\n\n".join(context_parts) if context_parts else ""