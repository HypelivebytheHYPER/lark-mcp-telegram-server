from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter()

# Use internal base for proxying requests
INTERNAL_BASE = os.getenv("MCP_BRIDGE_INTERNAL_BASE", "https://lark-mcp-telegram-server.onrender.com")

# MCP tool name -> (HTTP method, REST path)
TOOL_MAP = {
    # Lark messaging
    "im.v1.message.create": ("POST", "/api/v1/lark/send"),
    "lark_tenant_im_v1_message_create": ("POST", "/api/v1/lark/send"),
    "send_lark_message": ("POST", "/api/v1/lark/send"),
    # Bitable CRUD (adjust to match your actual endpoints)
    "bitable.v1.appTableRecord.search": ("GET", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records"),
    "bitable.v1.appTableRecord.create": ("POST", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/create"),
    "bitable.v1.appTableRecord.update": ("PUT", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}"),
    "bitable.v1.appTableRecord.delete": ("DELETE", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/{record_id}"),
    "bitable.v1.appTableRecord.batchCreate": ("POST", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/create"),
    "bitable.v1.appTableRecord.batchUpdate": ("PATCH", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/update"),
    "bitable.v1.appTableRecord.batchDelete": ("DELETE", "/api/v1/bitable/apps/{app_token}/tables/{table_id}/records/batch/delete"),
    # Add more mappings as needed
}

def ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def err(id_, code, msg):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": msg}}

@router.post("/invoke")
async def mcp_invoke(req: Request):
    body = await req.json()
    mid = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    if method == "tools/list":
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{INTERNAL_BASE}/mcp/tools")
            try:
                tools = r.json().get("tools", [])
            except Exception:
                return err(mid, -32000, f"Upstream tools error: {r.text[:200]}")
        return ok(mid, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if name not in TOOL_MAP:
            return err(mid, -32601, f"Tool not found: {name}")
        http_method, path = TOOL_MAP[name]
        # Fill in path params from args if needed
        for k, v in args.items():
            path = path.replace(f"{{{k}}}", str(v))
        url = f"{INTERNAL_BASE}{path}"
        async with httpx.AsyncClient(timeout=30) as c:
            if http_method == "POST":
                r = await c.post(url, json=args)
            elif http_method == "GET":
                r = await c.get(url, params=args)
            elif http_method == "PUT":
                r = await c.put(url, json=args)
            elif http_method == "PATCH":
                r = await c.patch(url, json=args)
            elif http_method == "DELETE":
                r = await c.delete(url, json=args)
            else:
                return err(mid, -32602, f"Unsupported HTTP method: {http_method}")
        try:
            data = r.json()
        except Exception:
            data = {"status_code": r.status_code, "text": r.text[:500]}
        return ok(mid, data)

    return err(mid, -32601, f"Method not found: {method}")
