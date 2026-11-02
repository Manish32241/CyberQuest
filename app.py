import hmac
import json
import os
import random
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for


MISSIONS: list[dict[str, Any]] = [
    {
        "title": "Password Cracker",
        "category": "Password security",
        "difficulty": "Easy",
        "description": "Build better habits for protecting your accounts.",
        "icon": "🔐",
        "xp": 30,
        "coins": 15,
        "time": 90,
        "questions": [
            {
                "question": "Which password is the strongest?",
                "options": ["password123", "12345678", "M@rS!9qL#2v", "qwerty"],
                "answer": "M@rS!9qL#2v",
                "hint": "Use uppercase, lowercase, numbers and symbols.",
            },
            {
                "question": "What is phishing?",
                "options": [
                    "A type of firewall",
                    "A trick to steal sensitive information",
                    "A programming language",
                    "A computer upgrade",
                ],
                "answer": "A trick to steal sensitive information",
                "hint": "It often involves fake emails or websites.",
            },
            {
                "question": "What should you do if a website offers HTTPS?",
                "options": [
                    "Trust everything on the website",
                    "Share all your passwords",
                    "Check the website identity and connection",
                    "Disable your antivirus",
                ],
                "answer": "Check the website identity and connection",
                "hint": "HTTPS protects the connection, but does not guarantee trustworthiness.",
            },
            {
                "question": "What is the safest way to store passwords?",
                "options": [
                    "In a public document",
                    "Using a reputable password manager",
                    "In a social media post",
                    "Using the same password everywhere",
                ],
                "answer": "Using a reputable password manager",
                "hint": "Use a tool designed to securely manage unique passwords.",
            },
            {
                "question": "What does two-factor authentication provide?",
                "options": [
                    "An extra verification step",
                    "Faster internet",
                    "Unlimited storage",
                    "A stronger screen",
                ],
                "answer": "An extra verification step",
                "hint": "It adds another way to verify your identity.",
            },
        ],
    },
    {
        "title": "Logic Breaker",
        "category": "Logic puzzles",
        "difficulty": "Easy",
        "description": "Spot patterns and sharpen your problem-solving skills.",
        "icon": "🧩",
        "xp": 30,
        "coins": 15,
        "time": 90,
        "questions": [
            {
                "question": "What number comes next? 2, 4, 8, 16, ?",
                "options": ["18", "24", "32", "30"],
                "answer": "32",
                "hint": "Each number is multiplied by 2.",
            },
            {
                "question": "What number comes next? 3, 6, 9, 12, ?",
                "options": ["13", "14", "15", "18"],
                "answer": "15",
                "hint": "Add 3 each time.",
            },
            {
                "question": "If all Zips are Zaps, and all Zaps are Zops, are all Zips Zops?",
                "options": ["Yes", "No", "Cannot be determined", "Only sometimes"],
                "answer": "Yes",
                "hint": "Follow the two statements in order.",
            },
            {
                "question": "What number is missing? 5, 10, 15, ?, 25",
                "options": ["18", "20", "22", "30"],
                "answer": "20",
                "hint": "The numbers increase by 5.",
            },
            {
                "question": "A code has 3 digits. Each digit is 2. What is the code?",
                "options": ["222", "226", "322", "202"],
                "answer": "222",
                "hint": "Repeat the digit 2 three times.",
            },
        ],
    },
    {
        "title": "Binary Decoder",
        "category": "Binary logic",
        "difficulty": "Medium",
        "description": "Decode binary numbers and uncover how computers count.",
        "icon": "⌘",
        "xp": 50,
        "coins": 25,
        "time": 100,
        "questions": [
            {
                "question": "What is the decimal value of binary 1010?",
                "options": ["8", "10", "12", "14"],
                "answer": "10",
                "hint": "Calculate 1×8 + 0×4 + 1×2 + 0×1.",
            },
            {
                "question": "What is binary 11 in decimal?",
                "options": ["2", "3", "4", "5"],
                "answer": "3",
                "hint": "Add the place values 2 and 1.",
            },
            {
                "question": "What is the binary representation of decimal 5?",
                "options": ["101", "110", "111", "100"],
                "answer": "101",
                "hint": "Four plus one equals five.",
            },
            {
                "question": "How many bits are in one byte?",
                "options": ["4", "8", "16", "32"],
                "answer": "8",
                "hint": "A byte contains eight binary digits.",
            },
            {
                "question": "What is binary 1000 in decimal?",
                "options": ["4", "6", "8", "10"],
                "answer": "8",
                "hint": "The leftmost 1 represents eight.",
            },
        ],
    },
    {
        "title": "Code Detective",
        "category": "JavaScript",
        "difficulty": "Medium",
        "description": "Read small programs and predict exactly what they do.",
        "icon": "</>",
        "xp": 50,
        "coins": 25,
        "time": 100,
        "questions": [
            {
                "question": "What does this code print?\n\nlet x = 5;\nx = x + 3;\nconsole.log(x);",
                "options": ["5", "8", "15", "Error"],
                "answer": "8",
                "hint": "Add 3 to the original value of x.",
            },
            {
                "question": "What does console.log(2 + 3) print?",
                "options": ["23", "5", "6", "Error"],
                "answer": "5",
                "hint": "Both values are numbers, so they are added.",
            },
            {
                "question": "What does console.log(10 > 5) print?",
                "options": ["true", "false", "10", "Error"],
                "answer": "true",
                "hint": "Ten is greater than five.",
            },
            {
                "question": "What is the result of 10 % 3 in JavaScript?",
                "options": ["1", "3", "0", "10"],
                "answer": "1",
                "hint": "The modulo operator returns the remainder.",
            },
            {
                "question": "What does console.log('Hi'.length) print?",
                "options": ["1", "2", "3", "Hi"],
                "answer": "2",
                "hint": "Count the characters in the string.",
            },
        ],
    },
    {
        "title": "Access Protocol",
        "category": "Conditional logic",
        "difficulty": "Hard",
        "description": "Make the right call in access-control scenarios.",
        "icon": "◈",
        "xp": 70,
        "coins": 35,
        "time": 120,
        "questions": [
            {
                "question": "A system accepts numbers greater than 10 and less than 20. Which value is valid?",
                "options": ["10", "20", "15", "25"],
                "answer": "15",
                "hint": "The number must be strictly between 10 and 20.",
            },
            {
                "question": "Which operator checks strict equality in JavaScript?",
                "options": ["=", "===", "!=", "=>"],
                "answer": "===",
                "hint": "It checks both value and type.",
            },
            {
                "question": "What is the result of !true in JavaScript?",
                "options": ["true", "false", "null", "undefined"],
                "answer": "false",
                "hint": "The ! operator reverses a boolean value.",
            },
            {
                "question": "Which condition checks whether age is at least 18?",
                "options": ["age < 18", "age === 18", "age >= 18", "age != 18"],
                "answer": "age >= 18",
                "hint": "Use the greater-than-or-equal operator.",
            },
            {
                "question": "What is the result of (5 > 3 && 2 < 4)?",
                "options": ["true", "false", "5", "Error"],
                "answer": "true",
                "hint": "Both comparisons are true, and && requires both.",
            },
        ],
    },
    {
        "title": "Final Firewall",
        "category": "Final challenge",
        "difficulty": "Hard",
        "description": "Bring your coding knowledge together for the final test.",
        "icon": "🛡",
        "xp": 100,
        "coins": 50,
        "time": 120,
        "questions": [
            {
                "question": "What does this loop print?\n\nfor (let i = 1; i <= 3; i++) {\n    console.log(i);\n}",
                "options": ["1 2 3", "0 1 2", "1 2", "3 3 3"],
                "answer": "1 2 3",
                "hint": "The loop starts at 1 and ends at 3.",
            },
            {
                "question": "Which method adds an item to the end of a JavaScript array?",
                "options": ["push()", "pop()", "shift()", "join()"],
                "answer": "push()",
                "hint": "It pushes a new element onto the end.",
            },
            {
                "question": "What does Boolean(0) return in JavaScript?",
                "options": ["true", "false", "0", "null"],
                "answer": "false",
                "hint": "Zero is a falsy value in JavaScript.",
            },
            {
                "question": "Which keyword declares a block-scoped variable that can be reassigned?",
                "options": ["const", "let", "static", "define"],
                "answer": "let",
                "hint": "This keyword allows reassignment within its scope.",
            },
            {
                "question": "What does [1, 2, 3].length return?",
                "options": ["2", "3", "4", "6"],
                "answer": "3",
                "hint": "Count the elements in the array.",
            },
        ],
    },
]

BADGES = [
    {"id": "first", "name": "First Mission", "icon": "🎯"},
    {"id": "streak", "name": "Combo Master", "icon": "🔥"},
    {"id": "five", "name": "Mission Veteran", "icon": "🛡️"},
    {"id": "xp", "name": "XP Hunter", "icon": "⚡"},
    {"id": "all", "name": "Elite Operative", "icon": "👑"},
]


def default_state() -> dict[str, Any]:
    return {
        "xp": 0,
        "coins": 0,
        "streak": 0,
        "best_streak": 0,
        "completed": [],
        "badges": [],
    }


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    instance_dir = Path(app.instance_path)
    instance_dir.mkdir(parents=True, exist_ok=True)
    secret_file = instance_dir / "secret_key"
    secret_key = os.environ.get("CYBERQUEST_SECRET_KEY")
    if not secret_key:
        if not secret_file.exists():
            secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
        secret_key = secret_file.read_text(encoding="utf-8").strip()

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=str(instance_dir / "cyberquest.sqlite"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    @contextmanager
    def connect_db() -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(app.config["DATABASE"], timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_progress (
                player_id TEXT PRIMARY KEY,
                progress_json TEXT NOT NULL
            )
            """
        )

    def player_id() -> str:
        current_id = session.get("player_id")
        if not isinstance(current_id, str):
            current_id = uuid.uuid4().hex
            session["player_id"] = current_id
        return current_id

    def load_state() -> dict[str, Any]:
        with connect_db() as connection:
            row = connection.execute(
                "SELECT progress_json FROM player_progress WHERE player_id = ?",
                (player_id(),),
            ).fetchone()
        if row is None:
            return default_state()

        try:
            saved = json.loads(row["progress_json"])
        except (json.JSONDecodeError, TypeError):
            return default_state()
        if not isinstance(saved, dict):
            return default_state()

        state = default_state()
        for key in ("xp", "coins", "streak", "best_streak"):
            value = saved.get(key)
            if type(value) is int and value >= 0:
                state[key] = value
        completed = saved.get("completed")
        if isinstance(completed, list):
            state["completed"] = sorted(
                {
                    index
                    for index in completed
                    if type(index) is int and 0 <= index < len(MISSIONS)
                }
            )
        badges = saved.get("badges")
        if isinstance(badges, list):
            valid_badges = {badge["id"] for badge in BADGES}
            state["badges"] = list(
                dict.fromkeys(
                    badge_id
                    for badge_id in badges
                    if isinstance(badge_id, str) and badge_id in valid_badges
                )
            )
        return state

    def save_state(state: dict[str, Any]) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO player_progress (player_id, progress_json)
                VALUES (?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    progress_json = excluded.progress_json
                """,
                (player_id(), json.dumps(state)),
            )

    def rank_for(xp: int) -> str:
        if xp >= 300:
            return "Elite Hacker"
        if xp >= 150:
            return "Cyber Agent"
        if xp >= 50:
            return "Code Runner"
        return "Script Kiddie"

    def award_badges(state: dict[str, Any]) -> list[str]:
        count = len(state["completed"])
        earned = set(state["badges"])
        criteria = {
            "first": count >= 1,
            "streak": state["best_streak"] >= 3,
            "five": count >= 5,
            "xp": state["xp"] >= 200,
            "all": count == len(MISSIONS),
        }
        new_badges: list[str] = []
        for badge in BADGES:
            if criteria[badge["id"]] and badge["id"] not in earned:
                state["badges"].append(badge["id"])
                new_badges.append(badge["name"])
        return new_badges

    def active_game() -> dict[str, Any] | None:
        game = session.get("game")
        if not isinstance(game, dict):
            return None
        mission_index = game.get("mission")
        question_indexes = game.get("questions")
        question_index = game.get("question_index")
        if (
            type(mission_index) is not int
            or not 0 <= mission_index < len(MISSIONS)
            or not isinstance(question_indexes, list)
            or len(question_indexes) != 3
            or any(
                type(index) is not int
                or not 0 <= index < len(MISSIONS[mission_index]["questions"])
                for index in question_indexes
            )
            or type(question_index) is not int
            or not 0 <= question_index < 3
            or type(game.get("deadline")) not in (int, float)
        ):
            session.pop("game", None)
            return None
        return game

    def expire_game(state: dict[str, Any], game: dict[str, Any]) -> bool:
        if time.time() < game["deadline"]:
            return False
        state["streak"] = 0
        save_state(state)
        session.pop("game", None)
        flash("Time expired. Your streak has reset.", "error")
        return True

    @app.before_request
    def protect_forms() -> None:
        token = session.get("csrf_token")
        if not isinstance(token, str):
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            if not hmac.compare_digest(token, submitted_token):
                abort(400, description="The form expired. Refresh the page and try again.")

    @app.get("/")
    def home():
        state = load_state()
        game = active_game()
        if game and expire_game(state, game):
            game = None

        completed = set(state["completed"])
        progress = state["xp"] % 100
        current_mission = MISSIONS[game["mission"]] if game else None
        question = None
        remaining = 0
        if game and current_mission:
            question_number = game["question_index"]
            question = current_mission["questions"][
                game["questions"][question_number]
            ]
            remaining = max(0, int(game["deadline"] - time.time() + 0.999))

        mission_cards = [
            {
                **mission,
                "index": index,
                "completed": index in completed,
                "unlocked": index == 0 or index - 1 in completed,
            }
            for index, mission in enumerate(MISSIONS)
        ]
        badges = [
            {**badge, "earned": badge["id"] in state["badges"]}
            for badge in BADGES
        ]
        return render_template(
            "index.html",
            state=state,
            rank=rank_for(state["xp"]),
            level=state["xp"] // 100 + 1,
            progress=progress,
            missions=mission_cards,
            badges=badges,
            game=game,
            mission=current_mission,
            question=question,
            remaining=remaining,
            csrf_token=session["csrf_token"],
        )

    @app.post("/mission/<int:index>/start")
    def start_mission(index: int):
        state = load_state()
        if index < 0 or index >= len(MISSIONS):
            abort(404)
        if active_game():
            flash("Finish or exit your current mission first.", "warning")
        elif index in state["completed"]:
            flash("That mission is already complete.", "info")
        elif index > 0 and index - 1 not in state["completed"]:
            flash("Complete the previous mission to unlock this one.", "warning")
        else:
            mission = MISSIONS[index]
            session["game"] = {
                "mission": index,
                "questions": random.sample(range(len(mission["questions"])), 3),
                "question_index": 0,
                "deadline": time.time() + mission["time"],
                "hint_used": False,
            }
            flash(f"{mission['title']} started. Good luck, operative.", "success")
        return redirect(url_for("home"))

    @app.post("/answer")
    def submit_answer():
        game = active_game()
        if not game:
            flash("Start a mission before submitting an answer.", "warning")
            return redirect(url_for("home"))
        state = load_state()
        if expire_game(state, game):
            return redirect(url_for("home"))

        mission = MISSIONS[game["mission"]]
        question = mission["questions"][game["questions"][game["question_index"]]]
        answer = request.form.get("answer", "")
        if answer not in question["options"]:
            flash("Choose an answer before continuing.", "warning")
            return redirect(url_for("home"))

        if answer != question["answer"]:
            state["streak"] = 0
            save_state(state)
            session.pop("game", None)
            flash("Not quite. Your streak has reset. Start again for a new set of questions.", "error")
            return redirect(url_for("home"))

        if game["question_index"] < 2:
            game["question_index"] += 1
            session["game"] = game
            flash("Correct answer. Keep going!", "success")
            return redirect(url_for("home"))

        previous_rank = rank_for(state["xp"])
        speed_bonus = max(
            0, int((game["deadline"] - time.time()) / mission["time"] * 20)
        )
        streak_bonus = state["streak"] * 5
        reward = mission["xp"] + speed_bonus + streak_bonus
        state["xp"] += reward
        state["coins"] += mission["coins"]
        state["streak"] += 1
        state["best_streak"] = max(state["best_streak"], state["streak"])
        state["completed"].append(game["mission"])
        new_badges = award_badges(state)
        save_state(state)
        session.pop("game", None)

        message = (
            f"Mission complete! +{reward} XP, +{mission['coins']} coins "
            f"(including a {speed_bonus} XP speed bonus)."
        )
        if previous_rank != rank_for(state["xp"]):
            message += f" Rank up: {rank_for(state['xp'])}!"
        if new_badges:
            message += f" Badge unlocked: {', '.join(new_badges)}!"
        if len(state["completed"]) == len(MISSIONS):
            message += " All missions complete. Elite operative!"
        flash(message, "success")
        return redirect(url_for("home"))

    @app.post("/hint")
    def use_hint():
        game = active_game()
        if not game:
            flash("Start a mission before requesting a hint.", "warning")
            return redirect(url_for("home"))
        state = load_state()
        if expire_game(state, game):
            return redirect(url_for("home"))
        if game.get("hint_used"):
            flash("You have already used a hint in this mission.", "info")
        elif state["coins"] < 5:
            flash("You need 5 coins to use a hint.", "error")
        else:
            state["coins"] -= 5
            game["hint_used"] = True
            session["game"] = game
            save_state(state)
            question = MISSIONS[game["mission"]]["questions"][
                game["questions"][game["question_index"]]
            ]
            flash(f"Hint: {question['hint']}", "hint")
        return redirect(url_for("home"))

    @app.post("/quit")
    def quit_mission():
        if active_game():
            state = load_state()
            state["streak"] = 0
            save_state(state)
            session.pop("game", None)
            flash("Mission exited. Your streak has reset.", "info")
        return redirect(url_for("home"))

    @app.post("/reset")
    def reset_progress():
        save_state(default_state())
        session.pop("game", None)
        flash("Your progress has been reset.", "info")
        return redirect(url_for("home"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
