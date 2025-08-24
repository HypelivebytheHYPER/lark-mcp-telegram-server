from fastapi import APIRouter, Request
import httpx, os

router = APIRouter()
INTERNAL_BASE = os.getenv("INTERNAL_BASE", "http://127.0.0.1:10000")  # หรือใช้ https://<your-render>

TOOL_MAP = {
    # Lark messaging
    "im.v1.message.create": ("POST", "/api/v1/lark/send"),
    "lark_tenant_im_v1_message_create": ("POST", "/api/v1/lark/send"),
    "send_lark_message": ("POST", "/api/v1/lark/send"),
    # Bitable (ปรับตามของคุณ)
    "bitable.v1.appTableRecord.search": ("POST", "/api/v1/bitable/search"),
    "bitable.v1.appTableRecord.create": ("POST", "/api/v1/bitable/create"),
    "bitable.v1.appTableRecord.update": ("POST", "/api/v1/bitable/update"),
    "bitable.v1.appTableRecord.batchCreate": ("POST", "/api/v1/bitable/batchCreate"),
    "bitable.v1.appTableRecord.batchDelete": ("POST", "/api/v1/bitable/batchDelete"),
}

def ok(i, r): return {"jsonrpc":"2.0","id":i,"result":r}
def er(i, c, m): return {"jsonrpc":"2.0","id":i,"error":{"code":c,"message":m}}

@router.post("/invoke")
async def invoke(req: Request):
    body = await req.json()
    mid, method = body.get("id"), body.get("method")
    params = body.get("params") or {}

    if method == "tools/list":
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{INTERNAL_BASE}/mcp/tools")
        try:
            tools = r.json().get("tools", [])
        except Exception:
            return er(mid, -32000, f"Upstream tools error: {r.text[:200]}")
        return ok(mid, {"tools": tools})

    if method == "tools/call":
        name = params.get("name"); args = params.get("arguments", {})
        if name not in TOOL_MAP:
            return er(mid, -32601, f"Tool not found: {name}")
        method_, path = TOOL_MAP[name]
        async with httpx.AsyncClient(timeout=30) as c:
            r = await (c.post(f"{INTERNAL_BASE}{path}", json=args) if method_=="POST"
                       else c.get(f"{INTERNAL_BASE}{path}", params=args))
        try:
            data = r.json()
        except Exception:
            data = {"status_code": r.status_code, "text": r.text[:500]}
        return ok(mid, data)

    return er(mid, -32601, f"Method not found: {method}")
