import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import random
import uvicorn
from dotenv import load_dotenv
import os

import words_mod


# Game settings
class GameSettings:
    round_duration = 120  # Total round time in seconds (3 minutes)
    gameplay_duration = 90  # Gameplay time in seconds (2 minutes)
    submission_window = 92  # Score submission window in seconds
    scores_ready_offset = 95  # Time when scores are ready for fetch


# Game state
class GameState:
    def __init__(self, chosen_words_file,all_words_file):
        self.chosen_words_list = words_mod.load_words(chosen_words_file)
        #self.all_words_list = words_mod.load_words(all_words_file)

        self.current_word = ""
        self.answers = []
        self.scores = []
        self.round_end_time = None
        self.score_submission_deadline = None
        self.scores_ready_time = None

    def start_new_round(self):
        """

        :rtype: object
        """
        self.current_word = random.choice(self.chosen_words_list)
        self.current_word = words_mod.ShuffleString(self.current_word)
        #self.current_word = "burglar"
        #self.answers = words_mod.generate_valid_words(self.current_word,self.all_words_list,3)
       # print(len(self.answers))
        self.scores = []

        now = datetime.utcnow()
        self.round_end_time = now + timedelta(seconds=GameSettings.round_duration)
        self.score_submission_deadline = now + timedelta(seconds=GameSettings.submission_window)
        self.scores_ready_time = now + timedelta(seconds=GameSettings.scores_ready_offset)
        print(f"New round started with word: {self.current_word}")


game_state = GameState("data/7_letter_popular_words_without_s.txt",
                       "data/3_plus_letter_words.txt")


async def manage_rounds():
    while True:
        game_state.start_new_round()  # Start a new round
        await asyncio.sleep(GameSettings.round_duration)  # Wait for the round duration to elapse


# Pydantic model for score submission
class ScoreSubmission(BaseModel):
    player_name: str
    score: int
    word: str


# FastAPI app setup with lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    #game_state.start_new_round()  # Start the first game round on startup
    print("Server startup")
    asyncio.create_task(manage_rounds())

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
            "answers" : game_state.answers,
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

@app.get("/testme")
async def testme():
    v = words_mod.generate_valid_words("burglar", game_state.all_words_list)
    return "gg"
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


@app.get("/get_scores")
async def get_scores():
    """Fetch the scores after the round ends."""
    if not game_state.scores_ready_time or datetime.utcnow() < game_state.scores_ready_time:
        return {"error": "Scores are not ready yet."}
    game_state.scores.sort(key=lambda x: x["score"], reverse=True)
    return {"scores": game_state.scores}


@app.post("/submit-score")
async def submit_score(submission: ScoreSubmission):
    """Submits the player's score for the round."""
    current_time = datetime.utcnow()
    if current_time > game_state.score_submission_deadline:
        raise HTTPException(status_code=400, detail="Score submission period has ended.")

    if submission.word != game_state.current_word:
        raise HTTPException(status_code=400, detail="Submitted word does not match the current round's word.")

    game_state.scores.append({"player": submission.player_name, "score": submission.score})
    return {"status": "Score submitted successfully"}

load_dotenv()
if os.getenv('uvicorn') == "1":
    if __name__ == "__main__":
        uvicorn.run("main:app", port=8080, host="127.0.0.1")
