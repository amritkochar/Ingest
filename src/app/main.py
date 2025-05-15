from fastapi import FastAPI, Header, HTTPException, Request
from ports.push_handler import BasePushHandler
from adapters.intercom_push import IntercomPushHandler
from services.ingest import ingest

app = FastAPI()
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/webhook/intercom/{tenant_id}")
async def intercom_webhook(
    tenant_id: str,
    request: Request,
    x_intercom_signature: str = Header(None),
):
    """
    Receives Intercom webhooks, normalizes, then ingests.
    """
    payload = await request.json()
    # Optionally validate x_intercom_signature here...
    # Inject tenant into payload for handler:
    payload["tenant_id"] = tenant_id

    handler: BasePushHandler = IntercomPushHandler()
    try:
        fb = await handler.handle(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    inserted = await ingest(fb)
    return {"status": "ok", "inserted": inserted}