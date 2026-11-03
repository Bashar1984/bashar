# hello-connector

A minimal MCP server (FastMCP, streamable HTTP) with one tool:

- `word_count(text)` — returns the number of whitespace-separated words in `text`.

## Run
```bash
pip install -r requirements.txt
python server.py
```
The server listens on `http://127.0.0.1:8000/mcp`. To use it as a Claude connector, expose it on a public HTTPS URL (e.g. a tunnel or a cloud host) and add that `/mcp` URL as a custom connector.

## Deploy to Render (free)
The repo includes a `render.yaml` blueprint.
1. Sign in at https://render.com with GitHub.
2. Click **New → Blueprint**, pick this repository and the branch that contains `render.yaml`, then click **Apply**.
3. When the deploy is live, copy the service address (e.g. `https://hello-connector-xxxx.onrender.com`).
4. In Claude: **Settings → Connectors → Add custom connector**, paste the address with `/mcp` at the end.

Note: free Render services sleep after ~15 minutes idle; the first request after that takes ~30–60 seconds.
