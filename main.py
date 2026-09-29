from fastapi import FastAPI

from api.model import router as model_router

app = FastAPI()
app.include_router(model_router)
