from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import random
import uvicorn
from dotenv import load_dotenv
import os




# Game settings
class GameSettings:
    round_duration = 3 * 60  # Total round time in seconds (3 minutes)
    gameplay_duration = 2 * 60  # Gameplay time in seconds (2 minutes)
    submission_window = 2 * 60 + 10  # Score submission window in seconds
    scores_ready_offset = 2 * 60 + 20  # Time when scores are ready for fetch


# Game state
class GameState:
    def __init__(self):
        self.current_word = ""
        self.scores = []
        self.round_end_time = None
        self.score_submission_deadline = None
        self.scores_ready_time = None

    def start_new_round(self):
        self.current_word = random.choice(["python", "fastapi", "async", "loop", "function"])
        self.scores = []

        now = datetime.utcnow()
        self.round_end_time = now + timedelta(seconds=GameSettings.round_duration)
        self.score_submission_deadline = now + timedelta(seconds=GameSettings.submission_window)
        self.scores_ready_time = now + timedelta(seconds=GameSettings.scores_ready_offset)
        print(f"New round started with word: {self.current_word}")


game_state = GameState()


# Pydantic model for score submission
class ScoreSubmission(BaseModel):
    player_name: str
    score: int
    word: str


# FastAPI app setup with lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    game_state.start_new_round()  # Start the first game round on startup
    print("Server startup: first game round started.")
    yield  # This is where the app runs
    print("Server shutdown: cleanup if necessary.")


app = FastAPI(lifespan=lifespan)


# API Endpoints
@app.get("/")
async def root():
    return {"message": "Hello"}

load_dotenv()
if os.getenv('uvicorn') == "1":
    if __name__ == "__main__":
        uvicorn.run("main:app", port=8080, host="127.0.0.1", reload=True)
