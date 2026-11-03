import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("hello-connector")

@mcp.tool()
def word_count(text: str) -> int:
    """Count the words in a block of text.
    Use when the user asks how long a draft is."""
    return len(text.split())

if __name__ == "__main__":
    # Hosts like Render set PORT; HOST=0.0.0.0 makes the server reachable from outside.
    mcp.run(
        transport="streamable-http",
        stateless_http=True,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
