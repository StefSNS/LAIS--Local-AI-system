# AI Engineer Roadmap (2026)

Source: https://roadmap.sh/ai-engineer

## Core Concepts

### Working With LLMs
- **Sampling Parameters**: Temperature, top_p, frequency penalty, presence penalty
- **Fine-tuning**: When and how to fine-tune models
- **Context Engineering**: System prompts, few-shot examples, context window management
  - Input Format: How to structure prompts
  - System Prompting: Define role, behavior, constraints
  - Context: Provide relevant background
  - Structured Output: Request JSON/schema
  - Function Calling: Tools/function definitions
  - Prompt Caching: Reuse static context
  - Streaming Responses: Handle token-by-token
  - Repetition Penalties: Avoid loops

### Type of Models
- **Closed Models**: Claude, GPT, Gemini
- **Self-Hosted Models**: Qwen, Phi-3, Gemma2
- **Open Source Models**: Hugging Face models

### Choosing the Right Model
- **Proprietary**: Claude (reasoning), GPT (general), Gemini (multimodal)
- **Open Source**: Qwen (fast), Phi-3 (reasoning), Gemma (efficient)

## Platforms & Ecosystem

### APIs & SDKs
- **Claude Messages API**
- **OpenAI-compatible APIs**
- **OpenRouter** (unified API for many models)

### MCP (Model Context Protocol)
- **MCP Host**: Host applications
- **MCP Server**: Provide context/tools
- **MCP Client**: Consume MCP servers
- **Data Layer**: State management
- **Transport Layer**: Communication
- **Building an MCP Server**: Implement tools/resources
- **Building an MCP Client**: Connect and use
- **Connect to Local Server**
- **Connect to Remote Server**

### Embeddings & Vector Databases
- **Embeddings**: Text → vector representations
- **Vector Databases**: Pinecone, Weaviate, Qdrant, Chroma
- **RAG (Retrieval Augmented Generation)**:
  - Query → Embed → Search → Context → LLM → Response
  - External Memory: Persist context across sessions
  - RAG and Dynamic Filters: Selective retrieval
  - Context compaction: Summarize/compress
  - Context Isolation: Separate concerns

## AI Agents
- **Multi-agents**: Multiple specialized agents collaborating
- **Agent frameworks**: AutoGen, CrewAI, LangGraph
- **Agent patterns**: ReAct, Plan-and-Execute, Tool Use

## AI Safety and Ethics
- Bias in models
- Hallucinations
- Prompt injection attacks
- Data privacy

## Other AI Applications
- **AI Assisted Coding Tools**: OpenCode, Cursor, Windsurf, Replit, Gemini
- **Vertex AI Agent Builder** (Google)
- **Google ADK** (Agent Development Kit)

## Python for AI Engineers
- **NumPy**: Array operations
- **Pandas**: Data manipulation
- **Hugging Face**: Model hub, transformers
- **PyTorch/TensorFlow**: Deep learning (if needed)
- **FastAPI**: Serving models as APIs
- **Pydantic**: Data validation for AI outputs
