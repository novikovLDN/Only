"""Health endpoint and webhooks for Railway."""

from fastapi import FastAPI

from app.api.webhooks.crypto import router as crypto_webhook_router

app = FastAPI()

app.include_router(crypto_webhook_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
