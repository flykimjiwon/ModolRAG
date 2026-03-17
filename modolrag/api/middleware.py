"""Middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Configure CORS and other middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # ModolAI or any frontend can call
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
