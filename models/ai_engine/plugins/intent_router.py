import sys
import importlib.util
from difflib import SequenceMatcher

sys.path.insert(0, "plugins")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    TFIDF_AVAILABLE = True
except ImportError:
    TFIDF_AVAILABLE = False

# ============ INTENT TRAINING DATA ============
INTENT_EXAMPLES = {
    "define": [
        "define this word",
        "what is the meaning of",
        "definition of",
        "tell me the meaning",
        "what does this word mean",
        "explain the term",
        "describe the concept",
        "what is"
    ],
    "research": [
        "research about this topic",
        "look up information on",
        "find out about",
        "learn about",
        "investigate this subject",
        "gather information on",
        "study this topic",
        "tell me about"
    ],
    "launch": [
        "open this application",
        "launch the program",
        "start the app",
        "run this software",
        "fire up the tool",
        "execute this program",
        "can you open",
        "please start"
    ],
    "code": [
        "write code for",
        "create a script that",
        "build a program",
        "make a function",
        "develop a tool",
        "code a solution",
        "write a python script",
        "program this for me"
    ],
    "search": [
        "search the web for",
        "search online for",
        "google this",
        "find online",
        "look this up on the internet",
        "browse for",
        "web search"
    ]
}

KEYWORDS = {
    "define": ["define", "meaning of", "definition of", "what does", "what is"],
    "research": ["research about", "look up", "find out about", "learn about"],
    "launch": ["open", "launch", "start", "run"],
    "code": ["write code", "make a script", "create a script", "write a program"],
    "search": ["search the web for", "search online for", "google search", "find online"],
    "browse": ["open website", "go to", "browse to", "visit", "open browser", "show me online", "open in browser"],
    "remember": ["remember that", "remember my", "note that", "keep in mind", "save this"],
    "scrape": ["deep research", "read the page", "extract from", "read website", "get content from", "analyse website"],
    "chat": []
}

FUZZY_THRESHOLD = 0.92
TFIDF_THRESHOLD = 0.35

# ============ BUILD TF-IDF MODEL ============
if TFIDF_AVAILABLE:
    all_examples = []
    all_labels = []
    for intent, examples in INTENT_EXAMPLES.items():
        for ex in examples:
            all_examples.append(ex)
            all_labels.append(intent)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_examples)


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# ============ CONTEXT ANALYZER ============
def analyze_context(message):
    """Deep analysis of message structure and meaning."""
    lower = message.lower().strip()
    words = lower.split()
    
    context = {
        "is_question": lower.endswith("?") or lower.startswith(("what", "how", "why", "when", "where", "who", "can", "could", "would")),
        "is_request": any(w in lower for w in ["please", "can you", "could you", "would you", "i need", "i want"]),
        "is_command": any(w in lower for w in ["do", "make", "create", "run", "execute", "write", "build"]),
        "has_target": len(words) > 1,
        "word_count": len(words),
        "polite": any(w in lower for w in ["please", "thank", "thanks", "kindly"]),
    }
    
    # Strip politeness prefixes for cleaner intent detection
    clean_msg = lower
    politeness = ["please ", "can you ", "could you ", "would you ", "i need you to ", "i want you to ", "kindly ", "hey ", "hi ", "hello "]
    for p in politeness:
        if clean_msg.startswith(p):
            clean_msg = clean_msg[len(p):]
    
    context["clean_message"] = clean_msg
    return context


# ============ TF-IDF INTENT SCORING ============
def tfidf_classify(message):
    """Use TF-IDF to score intent confidence."""
    if not TFIDF_AVAILABLE:
        return {}
    
    msg_vec = vectorizer.transform([message])
    scores = cosine_similarity(msg_vec, tfidf_matrix)[0]
    
    intent_scores = {}
    for i, score in enumerate(scores):
        label = all_labels[i]
        if label not in intent_scores or score > intent_scores[label]:
            intent_scores[label] = float(score)
    
    return intent_scores


# ============ MULTI-METHOD INTENT DETECTION ============
def detect_all_intents(message):
    """Combines keyword, fuzzy, and TF-IDF detection."""
    
    # Get context analysis
    ctx = analyze_context(message)
    clean_msg = ctx["clean_message"]
    lower_msg = clean_msg.lower()
    
    found = []
    seen_intents = set()

    # METHOD 1: Exact keyword matching
    for intent, words in KEYWORDS.items():
        for w in words:
            pos = lower_msg.find(w)
            if pos != -1:
                found.append({
                    "intent": intent,
                    "keyword": w,
                    "position": pos,
                    "method": "exact",
                    "confidence": 1.0
                })
                seen_intents.add(intent)
                break

    # METHOD 2: Fuzzy matching
    msg_words = lower_msg.split()
    for intent, words in KEYWORDS.items():
        if intent in seen_intents:
            continue
        if intent == "chat":
            continue
        for w in words:
            first_token = w.split()[0]
            for i, word in enumerate(msg_words):
                score = similarity(word, first_token)
                if score >= FUZZY_THRESHOLD:
                    found.append({
                        "intent": intent,
                        "keyword": first_token,
                        "position": i,
                        "method": "fuzzy",
                        "confidence": score
                    })
                    seen_intents.add(intent)
                    break
            if intent in seen_intents:
                break

        # METHOD 3: TF-IDF classification (excludes 'search' to prevent false positives)
    if TFIDF_AVAILABLE:
        tfidf_scores = tfidf_classify(clean_msg)
        for intent, score in tfidf_scores.items():
            if intent in ("search", "remember", "code", "browse", "scrape", "research"):
                continue  # Never auto-trigger search via TF-IDF
            if intent not in seen_intents and score >= TFIDF_THRESHOLD:
                found.append({
                    "intent": intent,
                    "keyword": "tfidf",
                    "position": 999,
                    "method": "tfidf",
                    "confidence": score
                })
                seen_intents.add(intent)

    # Sort by position (for execution order)
    found.sort(key=lambda x: x["position"])

    # Remove duplicates
    unique = []
    seen = set()
    for item in found:
        if item["intent"] not in seen:
            seen.add(item["intent"])
            unique.append(item)

    return unique, ctx


# ============ TOPIC EXTRACTION ============
def extract_topic(message, keyword, intent, ctx):
    """Extract topic with context awareness and filler removal."""
    clean = ctx["clean_message"]
    
    # ============ TF-IDF SPECIFIC HANDLING ============
    # When TF-IDF detected the intent, we need smarter extraction
    if keyword == "tfidf":
        lower_clean = clean.lower()
        words = clean.split()
        
        # Remove intent-related words to isolate the topic
        remove_words = [
            "i need", "i want", "can you", "could you", "please",
            "information about", "information on", "tell me about",
            "find out about", "look up", "research", "define",
            "open", "launch", "start", "search for", "find"
        ]
        
        topic = lower_clean
        for r in remove_words:
            topic = topic.replace(r, "").strip()
        
        # Clean punctuation and extra spaces
        topic = " ".join(topic.split()).strip(" ,.?!")
        return topic if topic else clean
    
    # ... rest of the existing function continues below
    lower_clean = clean.lower()
    words = clean.split()
    lower_words = lower_clean.split()

    # Try exact phrase match
    exact_pos = lower_clean.find(keyword.lower())
    if exact_pos != -1 and keyword != "tfidf":
        remaining = clean[exact_pos + len(keyword):].strip()
    else:
        # Fuzzy or TF-IDF: find best matching word and skip it
        start_idx = -1
        if keyword != "tfidf":
            for i, word in enumerate(lower_words):
                if similarity(word, keyword.split()[0]) >= FUZZY_THRESHOLD:
                    start_idx = i
                    break

        if start_idx != -1:
            remaining = ' '.join(words[start_idx + 1:])
        else:
            remaining = clean

    # Clean stop words
    stop_words = [" then ", " and then ", " after that ", " also ", " and "]
    lower_remaining = remaining.lower()
    cut = len(remaining)

    for stop in stop_words:
        idx = lower_remaining.find(stop)
        if idx != -1 and idx < cut:
            cut = idx

    topic = remaining[:cut].strip(" ,.?")

    # ============ INTENT-SPECIFIC CLEANING ============
    if intent == "define":
        # Remove common filler phrases
        filler = ["the word ", "the term ", "the concept ", "the meaning of ", "word ", "term ", "for me", "for us", "to me"]
        lower_topic = topic.lower()
        for f in filler:
            if lower_topic.startswith(f):
                topic = topic[len(f):].strip()
                lower_topic = topic.lower()
            if lower_topic.endswith(f.strip()):
                topic = topic[:-len(f.strip())].strip()
                lower_topic = topic.lower()
        # Take only the first word if multiple remain
        if ' ' in topic and len(topic.split()[0]) > 2:
            topic = topic.split()[0]

    elif intent == "launch":
        # Remove filler like "the app", "the program"
        filler = ["the app ", "the application ", "the program ", "app ", "application ", "program "]
        lower_topic = topic.lower()
        for f in filler:
            if lower_topic.startswith(f):
                topic = topic[len(f):].strip()
                lower_topic = topic.lower()

    elif intent == "research":
        # Remove filler like "information about", "more about"
        filler = ["information about ", "information on ", "more about ", "details on ", "details about "]
        lower_topic = topic.lower()
        for f in filler:
            if lower_topic.startswith(f):
                topic = topic[len(f):].strip()
                lower_topic = topic.lower()

    return topic.strip() if topic else remaining.strip()


# ============ INTENT EXECUTION ============
def execute_intent(intent, target):
    if intent == "define":
        spec = importlib.util.spec_from_file_location("dictionary", "plugins/dictionary.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.define(target)

    elif intent == "research":
        spec = importlib.util.spec_from_file_location("researcher", "plugins/researcher.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.research_and_save(target)

    elif intent == "launch":
        app = target.strip()
        if app and ".exe" not in app.lower():
            app += ".exe"
        spec = importlib.util.spec_from_file_location("system_control", "plugins/system_control.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.launch(app)

    elif intent == "code":
        spec = importlib.util.spec_from_file_location("agent_dispatcher", "plugins/agent_dispatcher.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.dispatch(target, "coder")

    elif intent == "search":
        spec = importlib.util.spec_from_file_location("web_search", "plugins/web_search.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.search(target)

    elif intent == "scrape":
        import sys
        sys.modules.pop("web_scraper", None)
        spec = importlib.util.spec_from_file_location("web_scraper", "plugins/web_scraper.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if target.startswith("http"):
            return mod.scrape_url(target)
        return mod.scrape_and_save(target)

    elif intent == "browse":
        import sys
        sys.modules.pop("browser_control", None)
        spec = importlib.util.spec_from_file_location("browser_control", "plugins/browser_control.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.open_search_engine(target)

    elif intent == "remember":
        import datetime, os
        os.makedirs("knowledge", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open("knowledge/personal_memory.md", "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {target}\n")
        return f"Noted and saved: {target}"

    return None


# ============ MAIN ROUTER ============
def route(message, llm_chat_func):
    intents, ctx = detect_all_intents(message)

    if not intents:
        return None, llm_chat_func(message)

    if len(intents) == 1:
        item = intents[0]
        intent = item["intent"]
        keyword = item["keyword"]
        confidence = item["confidence"]
        method = item["method"]
        topic = extract_topic(message, keyword, intent, ctx)

        try:
            result = execute_intent(intent, topic)
            label = f"{intent.upper()} ({method}, {confidence:.0%})"
            return label, str(result)
        except Exception as e:
            return f"{intent.upper()} ERROR", str(e)

    labels = []
    results = []

    for item in intents:
        intent = item["intent"]
        keyword = item["keyword"]
        confidence = item["confidence"]
        method = item["method"]
        topic = extract_topic(message, keyword, intent, ctx)

        try:
            result = execute_intent(intent, topic)
            labels.append(f"{intent.upper()} ({method}, {confidence:.0%})")
            results.append(f"── {intent.upper()} ({confidence:.0%}) ──\n{result}")
        except Exception as e:
            labels.append(f"{intent.upper()} ERROR")
            results.append(f"── {intent.upper()} ERROR ──\n{e}")

    return " + ".join(labels), "\n\n".join(results)