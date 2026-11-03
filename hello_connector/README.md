# hello-connector

A minimal MCP server (FastMCP, streamable HTTP) with one tool:

- `word_count(text)` — returns the number of whitespace-separated words in `text`.

## Run
```bash
pip install -r requirements.txt
python server.py
```
The server listens on `http://127.0.0.1:8000/mcp`. To use it as a Claude connector, expose it on a public HTTPS URL (e.g. a tunnel or a cloud host) and add that `/mcp` URL as a custom connector.
