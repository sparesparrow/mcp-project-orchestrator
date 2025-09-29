# PrintCast Agent 🎙️📄✉️

An automated voice-to-print service that integrates AI conversational agents with physical printing and delivery. Users can call a phone number, interact with an AI agent to select trending content (GitHub repos, RSS feeds, news), and have it printed and delivered to their address.

## 🌟 Features

- **Voice Interface**: Natural conversation through phone calls using ElevenLabs Conversational AI
- **Multi-language Support**: Czech and English language support
- **Content Sources**: 
  - GitHub Trending repositories
  - RSS feeds
  - News articles
- **Automated Printing**: CUPS integration for local/network printing
- **Delivery Integration**: Support for multiple carriers (Czech Post, Zásilkovna, DPD, PPL)
- **MCP Server**: Full Model Context Protocol implementation for AI client integration
- **Workflow Orchestration**: Complete automation from call to delivery

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Asterisk   │────▶│  ElevenLabs │────▶│   Content    │
│  SIP Server  │     │   AI Agent  │     │   Fetcher    │
└──────────────┘     └─────────────┘     └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   PrintCast    │
                    │   MCP Server   │
                    └───────┬────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
        ┌───────▼────┐ ┌───▼────┐ ┌────▼─────┐
        │   Print    │ │Delivery│ │   AWS    │
        │   Server   │ │Service │ │ Services │
        └────────────┘ └────────┘ └──────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Asterisk PBX (optional, for telephony)
- CUPS (optional, for printing)
- ElevenLabs API key
- Carrier API keys (for delivery services)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/printcast-agent.git
cd printcast-agent
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Configure environment

Create a `.env` file:

```bash
# Core settings
SERVER_NAME=PrintCast Agent
DEBUG=false

# Asterisk settings
ASTERISK_HOST=localhost
ASTERISK_PORT=5038
ASTERISK_USERNAME=admin
ASTERISK_PASSWORD=your_password

# ElevenLabs settings
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=voice_id

# Content sources
GITHUB_TOKEN=optional_token
NEWS_API_KEY=optional_key
RSS_FEEDS=https://news.ycombinator.com/rss,https://feeds.feedburner.com/TechCrunch/

# Printing
DEFAULT_PRINTER=default
CUPS_SERVER=localhost:631

# Delivery
DEFAULT_CARRIER=post
SENDER_NAME=PrintCast
SENDER_STREET=Your Street
SENDER_CITY=Your City
SENDER_POSTAL_CODE=12345
SENDER_COUNTRY=CZ

# Carrier APIs (optional)
ZASILKOVNA_API_KEY=your_key
DPD_API_KEY=your_key
PPL_API_KEY=your_key
```

### 4. Run the MCP server

```bash
python -m mcp_server.main
```

## 🐳 Docker Deployment

### Build the container

```bash
podman build -t printcast-agent -f Containerfile .
```

### Run with Podman

```bash
podman run -d \
  --name printcast \
  -p 8000:8000 \
  -p 5038:5038 \
  -p 5060:5060 \
  -v ./config:/app/config \
  --env-file .env \
  printcast-agent
```

## 📞 Workflow Example

1. **User calls the service** → Asterisk receives call
2. **AI agent greets user** → "Welcome to PrintCast! What would you like to print today?"
3. **Content selection** → User chooses GitHub trending, RSS, or news
4. **Agent reads options** → "Here are today's top 5 trending repositories..."
5. **User selects items** → Via voice or DTMF keys
6. **Address collection** → User provides delivery address
7. **Order confirmation** → Agent confirms selection and address
8. **Processing** → System generates PDF, prints, and arranges delivery
9. **Completion** → User receives tracking number via SMS

## 🛠️ MCP Tools Available

The server provides these MCP tools:

- `handle_incoming_call` - Process incoming phone calls
- `fetch_trending_content` - Get trending content from various sources
- `process_user_selection` - Handle user's content selection
- `generate_print_preview` - Create print preview
- `get_delivery_quote` - Get shipping cost estimate
- `end_call_session` - Terminate call session

## 📊 Monitoring

The server provides real-time monitoring through MCP resources:

- `resource://sessions/active` - Active call sessions
- `resource://config/services` - Service configuration status
- `resource://metrics/daily` - Daily usage metrics

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v --cov=src
```

## 📦 Project Structure

```
printcast-agent/
├── src/
│   ├── mcp_server/       # MCP server implementation
│   ├── integrations/      # Service integrations
│   │   ├── asterisk.py    # SIP/telephony
│   │   ├── elevenlabs.py  # AI voice agent
│   │   ├── content.py     # Content fetching
│   │   ├── printing.py    # Print management
│   │   └── delivery.py    # Shipping services
│   ├── orchestration/     # Workflow engine
│   └── utils/            # Utilities
├── config/               # Configuration files
├── scripts/              # Deployment scripts
├── tests/               # Test suite
├── Containerfile        # Container definition
└── pyproject.toml       # Project metadata
```

## 🤝 Integration with MCP Clients

### With Cursor Agent

```bash
# Add to Cursor's MCP settings
{
  "printcast": {
    "command": "python",
    "args": ["-m", "mcp_server.main"],
    "cwd": "/path/to/printcast-agent"
  }
}
```

### With Gemini CLI

```bash
# Configure Gemini to use PrintCast MCP server
gemini config add-server printcast http://localhost:8000
```

## 📚 API Documentation

### Starting a workflow

```python
# MCP tool call
await handle_incoming_call(
    caller_id="+420123456789",
    language="cs"
)
```

### Fetching content

```python
# Get trending GitHub repos
repos = await fetch_trending_content(
    content_type="github",
    limit=5,
    language="python"
)
```

### Processing order

```python
# Process user selection
result = await process_user_selection(
    session_id="call_20240101_120000",
    selected_items=["gh_openai_gpt", "gh_astro_framework"],
    delivery_address="Václavské náměstí 1, Praha, 11000",
    delivery_method="post"
)
```

## 🔒 Security Considerations

- All API keys should be kept secure
- Use HTTPS/TLS for production deployments
- Implement rate limiting for API endpoints
- Validate and sanitize all user inputs
- Regular security audits recommended

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- ElevenLabs for conversational AI capabilities
- Asterisk community for telephony infrastructure
- MCP protocol developers
- Open source contributors

## 📮 Contact

For questions and support:
- GitHub Issues: [Report bugs](https://github.com/yourusername/printcast-agent/issues)
- Email: team@printcast.ai

---

**PrintCast Agent** - Bridging the digital and physical worlds through voice 🎙️→📄→📮