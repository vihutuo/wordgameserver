from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
import os
app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

load_dotenv()
if os.getenv('uvicorn') == "1":
    if __name__ == "__main__":
        uvicorn.run("main:app", port=8080, host="127.0.0.1", reload=True)
