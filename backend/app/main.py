from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import ai, auth, books, health, scanner

app = FastAPI(
    title="Lexora API",
    description="Backend for Lexora — your AI-powered literary companion.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])


@app.get("/")
def root():
    return {"message": "Welcome to the Lexora API", "docs": "/docs"}
