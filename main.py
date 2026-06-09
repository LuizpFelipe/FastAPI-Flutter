import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from routers import (
    receita_router, 
    ingrediente_router, 
    receita_ingrediente_router, 
    inteligencia_router
)
from core.database import engine 

app = FastAPI(title="Minha API de Receitas")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(inteligencia_router.router, prefix="/inteligencia")
app.include_router(receita_router.router)
app.include_router(ingrediente_router.router)
app.include_router(receita_ingrediente_router.router)