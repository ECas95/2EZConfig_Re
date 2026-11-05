"""Stdlib-only integration tests for the opt-in local companion service."""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion_server import CompanionState, build_handler, serve


class CompanionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = CompanionState(str(Path(self.tmp.name) / "scores.sqlite3"))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(self.state, "secret"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.tmp.cleanup()

    def call(self, path, payload=None, token="secret", method=None):
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if payload is not None:
            headers["Content-Type"] = "application/json"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(self.url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=5) as resp:
                return resp.status, json.load(resp)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_local_dashboard_is_static_and_api_auth_remains_enforced(self):
        with urlopen(self.url + "/dashboard", timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("2EZ Companion", html)
            self.assertIn("connect-src 'self'", response.headers.get("Content-Security-Policy"))
        self.assertEqual(self.call("/api/v1/events", token=None)[0], 401)

    def test_health_requires_token(self):
        self.assertEqual(self.call("/health", token=None)[0], 401)
        self.assertEqual(self.call("/health", token="wrong")[0], 401)
        self.assertEqual(self.call("/health")[1]["status"], "ok")

    def test_score_store_and_leaderboard(self):
        score = {"game_id": "ez2dj_7th", "song_id": "own_song_001",
                 "chart_id": "5k_hd", "player_id": "local_1", "score": 1234567}
        status, result = self.call("/api/v1/scores", score)
        self.assertEqual(status, 201)
        self.assertFalse(result["verified"])
        score["score"] = 2345678
        self.assertEqual(self.call("/api/v1/scores", score)[0], 201)
        status, result = self.call(
            "/api/v1/leaderboard?game_id=ez2dj_7th&song_id=own_song_001&chart_id=5k_hd")
        self.assertEqual(status, 200)
        self.assertEqual([x["score"] for x in result["entries"]], [2345678, 1234567])
        self.assertFalse(result["verified"])

    def test_rejects_invalid_score_and_query(self):
        payload = {"game_id": "ez2dj_7th", "song_id": "../../escape",
                   "chart_id": "hd", "player_id": "p1", "score": 100}
        self.assertEqual(self.call("/api/v1/scores", payload)[0], 400)
        payload["song_id"] = "test"
        payload["score"] = True
        self.assertEqual(self.call("/api/v1/scores", payload)[0], 400)
        self.assertEqual(self.call("/api/v1/leaderboard?limit=wat")[0], 400)
        self.assertEqual(self.call("/api/v1/leaderboard?game_id=x&song_id=y&chart_id=z&limit=101")[0], 400)

    def test_lobby_ready_start_finish(self):
        _, room = self.call("/api/v1/lobbies", {
            "game_id": "ez2dj_7th", "song_id": "own_song_001", "chart_id": "5k_hd",
            "player_id": "p1", "mode": "versus", "max_players": 2
        })
        room_id = room["room_id"]
        endpoint = f"/api/v1/lobbies/{room_id}"
        self.assertEqual(self.call(endpoint + "/start", {"player_id": "p1"})[0], 400)
        self.assertEqual(self.call(endpoint + "/join", {"player_id": "p2"})[0], 201)
        self.assertEqual(self.call(endpoint + "/ready", {"player_id": "p1", "ready": True})[0], 201)
        self.assertEqual(self.call(endpoint + "/ready", {"player_id": "p2", "ready": True})[0], 201)
        self.assertEqual(self.call(endpoint + "/start", {"player_id": "p2"})[0], 400)
        self.assertEqual(self.call(endpoint + "/start", {"player_id": "p1"})[1]["status"], "started")
        self.assertEqual(self.call(endpoint + "/finish", {"player_id": "p1", "score": 500})[1]["status"], "started")
        self.assertEqual(self.call(endpoint + "/finish", {"player_id": "p2", "score": 400})[1]["status"], "finished")
        self.assertEqual(self.call(endpoint)[1]["players"]["p1"]["score"], 500)
        self.assertEqual(self.call(endpoint + "/finish", {"player_id": "p2", "score": 800})[0], 400)

    def test_event_viewer(self):
        self.assertEqual(self.call("/api/v1/events", {
            "event": "song.selected", "game_id": "ez2dj_7th",
            "data": {"song_id": "own_song_001"}})[0], 201)
        self.assertEqual(self.call("/api/v1/events")[1]["events"][0]["event"], "song.selected")
        self.assertEqual(self.call("/api/v1/events", {
            "event": "unknown.event", "game_id": "ez2dj_7th", "data": {}})[0], 400)

    def test_unauthenticated_remote_server_refused(self):
        with self.assertRaises(ValueError):
            serve(host="0.0.0.0", port=0, db=str(Path(self.tmp.name) / "remote.sqlite3"))


if __name__ == "__main__":
    unittest.main()
