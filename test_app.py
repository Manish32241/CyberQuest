import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import MISSIONS, create_app


class CyberQuestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.sqlite"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": str(database),
            }
        )
        self.client = self.app.test_client()
        self.csrf_token = self._csrf_token()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _csrf_token(self) -> str:
        with self.client.session_transaction() as browser_session:
            token = browser_session.get("csrf_token")
        if token is None:
            self.client.get("/")
            with self.client.session_transaction() as browser_session:
                token = browser_session["csrf_token"]
        return token

    def _post(self, path: str, **data: str):
        return self.client.post(path, data={"csrf_token": self.csrf_token, **data})

    def _query(self, query: str, parameters: tuple = ()) -> list[tuple]:
        with closing(sqlite3.connect(self.app.config["DATABASE"])) as connection:
            cursor = connection.execute(query, parameters)
            rows = cursor.fetchall()
            connection.commit()
            return rows

    def test_dashboard_shows_six_missions_and_initial_progress(self) -> None:
        response = self.client.get("/")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(page.count('class="panel mission-card'), len(MISSIONS))
        self.assertIn("Script Kiddie", page)
        self.assertIn("Password Cracker", page)

    def test_locked_mission_cannot_be_started(self) -> None:
        response = self._post("/mission/1/start")
        self.assertEqual(response.status_code, 302)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Complete the previous mission", page)
        with self.client.session_transaction() as browser_session:
            self.assertNotIn("game", browser_session)

    def test_completing_mission_saves_rewards_and_unlocks_next(self) -> None:
        self._post("/mission/0/start")
        with self.client.session_transaction() as browser_session:
            game = browser_session["game"]
        for question_index in game["questions"]:
            question = MISSIONS[0]["questions"][question_index]
            response = self._post("/answer", answer=question["answer"])
            self.assertEqual(response.status_code, 302)

        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Mission complete!", page)
        self.assertIn("First Mission", page)
        self.assertIn("Start mission", page)
        with self.client.session_transaction() as browser_session:
            player_id = browser_session["player_id"]
        progress_json = self._query(
            "SELECT progress_json FROM player_progress WHERE player_id = ?",
            (player_id,),
        )[0][0]
        progress = json.loads(progress_json)
        self.assertEqual(progress["completed"], [0])
        self.assertEqual(progress["coins"], MISSIONS[0]["coins"])
        self.assertGreaterEqual(progress["xp"], MISSIONS[0]["xp"])
        self.assertEqual(progress["streak"], 1)

    def test_hint_costs_coins_and_is_limited_to_once_per_mission(self) -> None:
        self._post("/mission/0/start")
        with self.client.session_transaction() as browser_session:
            game = browser_session["game"]
            game["deadline"] += 60
            browser_session["game"] = game
            player_id = browser_session["player_id"]
        self._query(
            "INSERT INTO player_progress VALUES (?, ?)",
            (player_id, '{"xp":0,"coins":10,"streak":0,"best_streak":0,"completed":[],"badges":[]}'),
        )

        self._post("/hint")
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Hint:", page)
        with self.client.session_transaction() as browser_session:
            self.assertTrue(browser_session["game"]["hint_used"])
        self._post("/hint")
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("already used a hint", page)

    def test_post_without_csrf_token_is_rejected(self) -> None:
        response = self.client.post("/mission/0/start")
        self.assertEqual(response.status_code, 400)

    def test_timer_expiry_resets_streak(self) -> None:
        self._post("/mission/0/start")
        with self.client.session_transaction() as browser_session:
            game = browser_session["game"]
            game["deadline"] = 0
            browser_session["game"] = game
            player_id = browser_session["player_id"]
        self._query(
            "INSERT INTO player_progress VALUES (?, ?)",
            (player_id, '{"xp":0,"coins":0,"streak":2,"best_streak":2,"completed":[],"badges":[]}'),
        )

        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Time expired", page)
        with self.client.session_transaction() as browser_session:
            self.assertNotIn("game", browser_session)
        progress_json = self._query(
            "SELECT progress_json FROM player_progress WHERE player_id = ?",
            (player_id,),
        )[0][0]
        self.assertEqual(json.loads(progress_json)["streak"], 0)


if __name__ == "__main__":
    unittest.main()
