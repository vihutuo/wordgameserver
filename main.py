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
    round_duration = 120  # Total round time in seconds (3 minutes)
    gameplay_duration = 90  # Gameplay time in seconds (2 minutes)
    submission_window = 95  # Score submission window in seconds
    scores_ready_offset = 100  # Time when scores are ready for fetch


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

@app.get("/game-state")
async def game_state_info():
    """Fetches the current game state with UTC timing information."""
    current_time = datetime.utcnow()
    if game_state.current_word and current_time < game_state.round_end_time:
        return {
            "round_status": "active",
            "current_word": game_state.current_word,
            "current_time_utc": current_time.isoformat() + "Z",
            "game_end_time_utc": game_state.round_end_time.isoformat() + "Z",
            "score_submission_deadline_utc": game_state.score_submission_deadline.isoformat() + "Z",
            "scores_ready_time_utc": game_state.scores_ready_time.isoformat() + "Z",
        }

    if game_state.round_end_time:
        time_until_next_round = (game_state.round_end_time - current_time).total_seconds()
        return {
            "round_status": "inactive",
            "time_until_next_round": max(0, time_until_next_round)
        }

    game_state.start_new_round()
    return {"round_status": "inactive", "time_until_next_round": GameSettings.round_duration}


@app.get("/fetch-word")
async def fetch_word():
    """Fetches the word for the current round, along with timing information as UTC timestamps."""
    current_time = datetime.utcnow()

    if not game_state.current_word:
        raise HTTPException(status_code=400, detail="No round is currently active.")

    return {
        "word": game_state.current_word,
        "current_time_utc": current_time.isoformat() + "Z",
        "game_end_time_utc": game_state.round_end_time.isoformat() + "Z",
        "score_submission_deadline_utc": game_state.score_submission_deadline.isoformat() + "Z",
        "scores_ready_time_utc": game_state.scores_ready_time.isoformat() + "Z",
    }


load_dotenv()
if os.getenv('uvicorn') == "1":
    if __name__ == "__main__":
        uvicorn.run("main:app", port=8080, host="127.0.0.1", reload=True)
