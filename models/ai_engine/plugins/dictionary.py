import os
import json

# Load the offline dictionary once into memory
DICT_PATH = 'knowledge/webster_dictionary.json'
_dictionary = None

def _load_dict():
    global _dictionary
    if _dictionary is None:
        try:
            with open(DICT_PATH, 'r', encoding='utf-8') as f:
                _dictionary = json.load(f)
        except Exception as e:
            _dictionary = {}
    return _dictionary

def define(word):
    """Look up a word in the offline Webster dictionary."""
    # Check if we already have a cached knowledge file
    cache_file = f"knowledge/dict_{word.lower()}.md"
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Search the offline dictionary
    dictionary = _load_dict()
    
    # Try exact match (case-insensitive)
    result = None
    for key in dictionary:
        if key.lower() == word.lower():
            result = dictionary[key]
            break
    
    if result:
        output = f"# Definition: {word}\n\n{result}\n"
        # Cache it for future retrieval
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(output)
        return output
    else:
        return f"'{word}' not found in offline dictionary."

def find_similar(word, max_results=5):
    """Find words that start with the same letters."""
    dictionary = _load_dict()
    prefix = word.lower()[:3]
    matches = []
    for key in dictionary:
        if key.lower().startswith(prefix):
            matches.append(key)
        if len(matches) >= max_results:
            break
    return matches

def word_count():
    """Return total words in the dictionary."""
    dictionary = _load_dict()
    return f"Offline dictionary contains {len(dictionary)} words."