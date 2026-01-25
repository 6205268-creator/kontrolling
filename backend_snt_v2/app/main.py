from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router

app = FastAPI(title="SNT Accounting v2 (physical persons, members, plots)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["v2"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
