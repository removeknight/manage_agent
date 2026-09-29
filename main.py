from fastapi import FastAPI

from api.model import router as model_router
from api.chat import router as chat_router

app = FastAPI()
app.include_router(model_router)
app.include_router(chat_router)
