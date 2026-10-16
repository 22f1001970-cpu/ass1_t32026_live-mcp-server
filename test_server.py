import asyncio
import hashlib
import httpx
from main import app, NORMALIZED_EMAIL


async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-03-26"}
        async def rpc(method, request_id, params=None, extra_headers=None):
            body = {"jsonrpc": "2.0", "id": request_id, "method": method}
            if params is not None:
                body["params"] = params
            response = await client.post("/mcp", json=body, headers={**headers, **(extra_headers or {})})
            response.raise_for_status()
            return response.json()

        assert (await rpc("initialize", 1, {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}))["result"]["capabilities"]["tools"] == {"listChanged": False}
        notice = await client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers)
        assert notice.status_code == 202
        tools = (await rpc("tools/list", 2))["result"]["tools"]
        assert len(tools) == 1 and tools[0]["name"] == "solve_challenge"
        for i in range(5):
            challenge = f"{i:032x}"
            reply = await rpc("tools/call", i + 3, {"name": "solve_challenge", "arguments": {}},
                              {"X-Exam-Challenge": challenge, "X-Exam-Timestamp": "1792150000000", "X-Exam-Signature": "example"})
            got = reply["result"]["content"][0]["text"]
            expected = hashlib.sha256(f"{challenge}:{NORMALIZED_EMAIL}".encode()).hexdigest()[:16]
            assert got == expected, (got, expected)
        print("PASS: initialize, initialized, tools/list and 5 unique challenge calls")

if __name__ == "__main__":
    asyncio.run(main())
