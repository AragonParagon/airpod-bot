# AirPods Assistant Bot 🎧

An AI-powered assistant specialized exclusively in Apple AirPods. Get expert help with comparisons, troubleshooting, recommendations, and specifications.

## Features

- **Streaming Chat API** - Real-time response streaming for better UX
- **Web Search Integration** - Answers backed by live web data via Tavily
- **Conversation Memory** - In-memory message persistence for contextual chats
- **Feedback System** - Collect user feedback via email (Resend)
- **Tool Call Streaming** - Stream both text and tool calls to frontend

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| AI | LangChain + LangGraph |
| LLM | Google Gemini / OpenAI |
| Search | Tavily API |
| Email | Resend |

## Project Structure

```
app/
├── agent/
│   ├── agent.py       # AirpodAgent class with LangGraph setup
│   └── tools.py       # Tavily web search tool
├── api/
│   ├── chat.py        # Chat endpoints (sync + streaming)
│   └── feedback.py    # Feedback endpoint
├── core/
│   └── settings.py    # Configuration and system prompt
├── models/
│   ├── chat.py        # Chat request/response models
│   └── feedback.py    # Feedback models
├── service/
│   ├── chat.py        # Chat business logic
│   └── feedback.py    # Feedback email service
├── utils/
│   └── store.py       # In-memory conversation store
└── main.py            # FastAPI app entrypoint
```

## Getting Started

### Prerequisites

- Python 3.12+
- API keys for:
  - Google AI (Gemini) or OpenAI
  - Tavily (web search)
  - Resend (email)

### Installation

```bash
# Clone and navigate
cd airpod-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env.google` file:

```env
# LLM Provider
LLM_PROVIDER=google
LLM_PROVIDER_API_KEY=your_google_api_key
LLM_PROVIDER_MODEL=gemini-2.0-flash

# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=your_tavily_api_key

# Email
RESEND_API_KEY=your_resend_api_key
RESEND_FEEDBACK_EMAIL=your_email@example.com

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`

## API Endpoints

### Chat (Blocking)
```
POST /api/v1/chat/
```
Synchronous chat endpoint. Waits for complete response.

**Request:**
```json
{
  "message": "Compare AirPods Pro 2 vs AirPods 3",
  "conversation_id": "abc-123"
}
```

### Chat (Streaming)
```
POST /api/v1/chat/stream
```
Real-time streaming via Server-Sent Events (SSE).

**Response format:**
```
data: {"type": "text", "node": "agent", "data": "Hello!"}
data: {"type": "tool_call", "node": "agent", "data": {"name": "tavily_search", "args": {...}}}
```

### Feedback
```
POST /api/v1/feedback/
```
Submit user feedback.

**Request:**
```json
{
  "message": "Great assistant!",
  "email": "user@example.com",
  "rating": 5
}
```

## Frontend Integration

### Consuming SSE Stream

```javascript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello', conversation_id: 'abc-123' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const lines = decoder.decode(value).split('\n\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      if (event.type === 'text') {
        console.log('Text:', event.data);
      } else if (event.type === 'tool_call') {
        console.log('Tool:', event.data.name);
      }
    }
  }
}
```

## Agent Capabilities

The AirPods Assistant can help with:

- **Comparisons** - Feature-by-feature model comparisons
- **Recommendations** - Personalized suggestions based on use case
- **Troubleshooting** - Step-by-step fixes for common issues
- **Specifications** - Accurate specs backed by web search
- **Compatibility** - iOS/device requirements and limitations

The agent will politely decline questions outside the AirPods domain.

## License

MIT
