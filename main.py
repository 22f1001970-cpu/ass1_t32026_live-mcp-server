"""Minimal stateless MCP Streamable HTTP server for the exam challenge."""
import hashlib
import os
import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="Live MCP Challenge Server")
NORMALIZED_EMAIL = "22f1001970@ds.study.iitm.ac.in"
PROTOCOL_VERSION = "2025-03-26"

TOOL = {
    "name": "solve_challenge",
    "description": "Solve the per-request challenge supplied in the X-Exam-Challenge HTTP header.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
}


def error(request_id, code, message, status_code=200):
    return JSONResponse({"jsonrpc": "2.0", "id": request_id,
                         "error": {"code": code, "message": message}}, status_code=status_code)


@app.post("/mcp")
async def mcp(request: Request):
    try:
        data = await request.json()
    except ValueError:
        return error(None, -32700, "Parse error", 400)
    if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
        return error(data.get("id") if isinstance(data, dict) else None,
                     -32600, "Invalid Request", 400)
    method = data.get("method")
    request_id = data.get("id")

    # JSON-RPC notifications have no request id and must not receive a result.
    if "id" not in data:
        return Response(status_code=202)

    if method == "initialize":
        return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "exam-challenge-mcp", "version": "1.0.0"},
        }})

    if method == "ping":
        return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {}})

    if method == "tools/list":
        return JSONResponse({"jsonrpc": "2.0", "id": request_id,
                             "result": {"tools": [TOOL]}})

    if method == "tools/call":
        params = data.get("params") or {}
        if not isinstance(params, dict) or params.get("name") != TOOL["name"]:
            return error(request_id, -32602, "Unknown tool")
        challenge = request.headers.get("x-exam-challenge", "")
        if not re.fullmatch(r"[0-9a-f]{32}", challenge):
            return error(request_id, -32602, "Missing or invalid X-Exam-Challenge header")
        # Signatures are optional and unscored; timestamp and signature are
        # intentionally not needed to compute the requested digest.
        value = hashlib.sha256(f"{challenge}:{NORMALIZED_EMAIL}".encode("utf-8")).hexdigest()[:16]
        return JSONResponse({"jsonrpc": "2.0", "id": request_id,
                             "result": {"content": [{"type": "text", "text": value}],
                                        "isError": False}})

    return error(request_id, -32601, "Method not found")


@app.get("/")
def home():
    return {"status": "ok", "mcp_endpoint": "/mcp"}


@app.get("/mcp")
def mcp_get():
    # Streamable HTTP servers without SSE streams may reject GET with 405.
    return Response(status_code=405)
