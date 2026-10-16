# Live MCP server (Streamable HTTP)

## Deploy to Render
1. Upload the files to a new GitHub repository.
2. Create a Render Web Service connected to the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Submit `https://YOUR-SERVICE.onrender.com/mcp` (not the root URL).

No API secret or environment variable is required. HMAC header checking is optional for the assignment.

## What this implements
- JSON-RPC 2.0 `initialize`, `notifications/initialized`, `tools/list`, and `tools/call` over `POST /mcp`.
- Exactly one MCP tool: `solve_challenge` with an empty object input schema.
- Reads each fresh `X-Exam-Challenge` from HTTP request headers and returns the first 16 hex chars of SHA-256 of `challenge:22f1001970@ds.study.iitm.ac.in` in one MCP text block.
- Stateless Streamable HTTP JSON responses; no session ID is required. GET /mcp returns 405 (no SSE stream).

## Local test
`uvicorn main:app --reload`

See `test_server.py` for a complete simulated MCP handshake and tool call.
