---
name: rag-implementation
description: Implement RAG (Retrieval Augmented Generation) pipelines. Use when user asks about RAG, vector databases, embeddings, or document retrieval.
---

# RAG Implementation Skill

## When to Use
- User asks about "RAG", "vector database", "embeddings"
- Need to search large document collections
- Adding knowledge base to LLM
- Implementing semantic search
- Building Q&A over documents

## RAG Pipeline (from roadmap.sh/AI-Engineer)

### Architecture
```
Query → Embed → Vector Search → Retrieve Context → LLM → Response
```

### Components
1. **Document Loader**: Read PDFs, MD, TXT
2. **Text Splitter**: Chunk documents (512-1024 tokens)
3. **Embeddings Model**: Convert text → vectors
4. **Vector Database**: Store + search vectors
5. **Retriever**: Find relevant chunks
6. **LLM**: Generate answer with context

## Vector Databases (from roadmap)

| Database | Best For | LangChain Support |
|----------|----------|-------------------|
| **Chroma** | Local, simple setup, prototyping | ✅ |
| **Pinecone** | Managed, scalable, production | ✅ |
| **Weaviate** | Production, multi-modal | ✅ |
| **Qdrant** | Rust-based, fast, filtering | ✅ |
| **FAISS** | In-memory, Facebook's library | ✅ |

## Implementation (Python)

### Basic RAG with LangChain
```python
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# 1. Load documents
loader = DirectoryLoader("knowledge/base/", glob="*.md")
docs = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)

# 3. Create embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 4. Store in vector DB
vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="db")

# 5. Retrieve + Generate
retriever = vectordb.as_retriever(search_kwargs={"k": 3})
```

### Query with Context
```python
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=retriever,
    return_source_documents=True
)

result = qa_chain("What are the security best practices?")
print(result["result"])
print(result["source_documents"])
```

## Embeddings Models

| Model | Speed | Quality | Size |
|-------|------|---------|------|
| **all-MiniLM-L6-v2** | Fast | Good | 80MB |
| **all-mpnet-base-v2** | Medium | Better | 420MB |
| **text-embedding-3-small** (OpenAI) | Fast | Great | API |
| **BGE models** | Medium | Great | Varies |

## Chunking Strategies

| Strategy | Chunk Size | Overlap | Best For |
|----------|-----------|--------|----------|
| **Fixed size** | 512 tokens | 50 | General docs |
| **Recursive** | 1024 tokens | 100 | Structured docs |
| **Semantic** | Variable | - | Complex topics |
| **By section** | Section-based | - | Markdown/HTML |

## Advanced Techniques

### HyDE (Hypothetical Document Embeddings)
```
1. Generate hypothetical answer (without context)
2. Embed the hypothetical answer
3. Search for similar real documents
4. Use real docs for final answer
```

### Reranking
```
1. Retrieve top-20 chunks (fast embedding)
2. Rerank with cross-encoder (accurate)
3. Use top-3 for LLM
```

### Context Compression
```
1. Retrieve relevant chunks
2. Compress with summary LLM
3. Pass compressed context to main LLM
```

## When NOT to Use RAG
- Small knowledge base (<100 docs) → Just add to prompt
- Real-time data → Use APIs/web search
- Simple Q&A → Direct prompting may suffice
- Very long documents → Summarize first

## Best Practices
- **Chunk size**: 512-1024 tokens (not too small/large)
- **Overlap**: 10-15% of chunk size
- **Metadata**: Store source, page, timestamp
- **Update freq**: Re-index when docs change
- **Evaluation**: Test with known queries
- **Hybrid search**: Combine keyword + semantic

## Tools & Libraries
- **LangChain**: High-level RAG abstractions
- **LlamaIndex**: Specialized for RAG
- **FAISS**: Facebook's vector search
- **Sentence-Transformers**: Embedding models
- **Chroma**: Simple local vector DB

## Integration with Omnis
```python
# In Omnis, use knowledge base as RAG source
from knowledge.memory.unified_memory import UnifiedMemory

# RAG can enhance context injection
memory = UnifiedMemory()
context = memory.get_context_with_rag(query="user question")
```
