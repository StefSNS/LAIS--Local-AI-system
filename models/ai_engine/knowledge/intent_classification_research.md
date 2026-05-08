# Research: Python Intent Classification Methods (2024)

## 1. Keyword-Based Matching (Current Method)
- Simple, fast, no dependencies
- Weakness: No fuzzy matching, no synonym detection
- Improvement: Add Levenshtein distance for typo tolerance

## 2. TF-IDF + Cosine Similarity
- Uses scikit-learn TfidfVectorizer
- Compares input to labeled examples
- Lightweight, works offline
- Strength: Can rank confidence of multiple intents

## 3. FuzzyWuzzy String Matching
- Python library for fuzzy string comparison
- Handles typos, partial matches, word order
- Very lightweight
- Improvement: Perfect for typo-tolerant keyword matching

## 4. spaCy NLP Pipeline
- Tokenization, lemmatization, named entity recognition
- Can extract topics more accurately
- Medium weight, offline capable
- Improvement: Better topic extraction from complex sentences

## 5. Synonym Expansion
- Build a synonym dictionary for each intent keyword
- Example: launch = open, start, run, execute, fire up
- No extra libraries needed
- Improvement: Massively expands natural language coverage