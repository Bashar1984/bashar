from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-connector", stateless_http=True)

@mcp.tool()
def word_count(text: str) -> int:
    """Count the words in a block of text.
    Use when the user asks how long a draft is."""
    return len(text.split())

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
