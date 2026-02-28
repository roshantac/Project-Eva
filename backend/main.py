"""Run the FastAPI app for the EVA Assistant."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from src.routers import chat_router


app = FastAPI(title="EVA Assistant", version="0.1.0")
app.include_router(chat_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
