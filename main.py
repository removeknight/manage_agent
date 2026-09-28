from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/chat")
async def chat():
    return {"Chat": "Ok"}

