from fastapi import FastAPI

from . import store
from .routers import calls, dashboard, knowledge, voice

store.init_db()

app = FastAPI(title="Contesta API", version="0.1.0",
              description="Recepcionista por voz 24/7 para clínicas, talleres y despachos")
app.include_router(calls.router)
app.include_router(knowledge.router)
app.include_router(voice.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "contesta"}
