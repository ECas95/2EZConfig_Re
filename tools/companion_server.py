#!/usr/bin/env python3
"""2EZConfig companion API (prototype): scores, local event viewer and lobbies.

No game instrumentation or network hooks are installed by this server.
Runs on a modern Python 3.10+ host, not on Windows XP.
"""
from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sqlite3
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_BODY = 16 * 1024
MAX_PLAYERS = 4
VALID_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.:"
CLEAR_TYPES = {"unknown", "failed", "clear", "full_combo", "perfect"}
ROOM_MODES = {"versus", "coop"}


def identifier(value, field, max_length=96):
    if not isinstance(value, str) or not 1 <= len(value) <= max_length:
        raise ValueError(f"{field} must be a nonempty string (max {max_length})")
    if any(char not in VALID_CHARS for char in value):
        raise ValueError(f"{field} has unsupported characters")
    return value


def integer(value, field, lower, upper):
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        raise ValueError(f"{field} must be an integer between {lower} and {upper}")
    return value


class CompanionState:
    """SQLite stores scores; in-memory lobbies are intentionally ephemeral."""

    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self.lock = threading.RLock()
        self.rooms: dict[str, dict] = {}
        self.events = deque(maxlen=100)
        self.init_database()

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def init_database(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  created_at INTEGER NOT NULL,
                  game_id TEXT NOT NULL,
                  song_id TEXT NOT NULL,
                  chart_id TEXT NOT NULL,
                  player_id TEXT NOT NULL,
                  score INTEGER NOT NULL,
                  clear_type TEXT NOT NULL
                )""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_scores_chart ON scores (game_id, song_id, chart_id, score DESC)")

    def add_score(self, payload):
        game = identifier(payload.get("game_id"), "game_id")
        song = identifier(payload.get("song_id"), "song_id")
        chart = identifier(payload.get("chart_id"), "chart_id")
        player = identifier(payload.get("player_id"), "player_id", 48)
        score = integer(payload.get("score"), "score", 0, 1_000_000_000)
        clear_type = payload.get("clear_type", "unknown")
        if clear_type not in CLEAR_TYPES:
            raise ValueError("unsupported clear_type")
        with self.connect() as con:
            cursor = con.execute(
                "INSERT INTO scores (created_at,game_id,song_id,chart_id,player_id,score,clear_type) "
                "VALUES (?,?,?,?,?,?,?)",
                (int(time.time()), game, song, chart, player, score, clear_type))
            return {"id": cursor.lastrowid, "stored": True, "verified": False}

    def leaderboard(self, query):
        game = identifier(query.get("game_id", [""])[0], "game_id")
        song = identifier(query.get("song_id", [""])[0], "song_id")
        chart = identifier(query.get("chart_id", [""])[0], "chart_id")
        limit = integer(int(query.get("limit", ["20"])[0]), "limit", 1, 100)
        with self.connect() as con:
            rows = con.execute(
                "SELECT player_id,score,clear_type,created_at FROM scores "
                "WHERE game_id=? AND song_id=? AND chart_id=? "
                "ORDER BY score DESC, created_at ASC, id ASC LIMIT ?",
                (game, song, chart, limit)).fetchall()
        return {"entries": [dict(row) for row in rows], "verified": False}

    def create_room(self, payload):
        game = identifier(payload.get("game_id"), "game_id")
        song = identifier(payload.get("song_id"), "song_id")
        chart = identifier(payload.get("chart_id"), "chart_id")
        host = identifier(payload.get("player_id"), "player_id", 48)
        mode = payload.get("mode", "versus")
        if mode not in ROOM_MODES:
            raise ValueError("mode must be versus or coop")
        max_players = integer(payload.get("max_players", 2), "max_players", 2, MAX_PLAYERS)
        room_id = secrets.token_hex(4)
        with self.lock:
            self.rooms[room_id] = {
                "room_id": room_id, "game_id": game, "song_id": song,
                "chart_id": chart, "mode": mode, "host": host,
                "max_players": max_players, "status": "waiting",
                "players": {host: {"ready": False, "score": None}}
            }
            return self.get_room(room_id)

    def get_room(self, room_id):
        with self.lock:
            room = self.rooms.get(room_id)
            if room is None:
                raise KeyError("lobby not found")
            return json.loads(json.dumps(room))

    def list_rooms(self):
        with self.lock:
            return {"lobbies": [self.get_room(x) for x in list(self.rooms)[:100]]}

    def join_room(self, room_id, payload):
        player = identifier(payload.get("player_id"), "player_id", 48)
        with self.lock:
            room = self.get_room(room_id)
            if room["status"] != "waiting":
                raise ValueError("lobby already started")
            if player not in room["players"] and len(room["players"]) >= room["max_players"]:
                raise ValueError("lobby is full")
            room["players"].setdefault(player, {"ready": False, "score": None})
            self.rooms[room_id] = room
            return self.get_room(room_id)

    def set_ready(self, room_id, payload):
        player = identifier(payload.get("player_id"), "player_id", 48)
        ready = payload.get("ready")
        if not isinstance(ready, bool):
            raise ValueError("ready must be a boolean")
        with self.lock:
            room = self.get_room(room_id)
            if room["status"] != "waiting" or player not in room["players"]:
                raise ValueError("player not in a waiting lobby")
            room["players"][player]["ready"] = ready
            self.rooms[room_id] = room
            return self.get_room(room_id)

    def start_room(self, room_id, payload):
        player = identifier(payload.get("player_id"), "player_id", 48)
        with self.lock:
            room = self.get_room(room_id)
            if player != room["host"]:
                raise ValueError("only the host may start a lobby")
            if room["status"] != "waiting" or len(room["players"]) < 2 or not all(
                member["ready"] for member in room["players"].values()
            ):
                raise ValueError("at least two ready players are required")
            room["status"] = "started"
            room["started_at"] = int(time.time())
            self.rooms[room_id] = room
            return self.get_room(room_id)

    def submit_room_score(self, room_id, payload):
        player = identifier(payload.get("player_id"), "player_id", 48)
        score = integer(payload.get("score"), "score", 0, 1_000_000_000)
        with self.lock:
            room = self.get_room(room_id)
            if room["status"] != "started" or player not in room["players"]:
                raise ValueError("lobby not started or player not joined")
            if room["players"][player]["score"] is not None:
                raise ValueError("score already submitted for this player")
            room["players"][player]["score"] = score
            if all(member["score"] is not None for member in room["players"].values()):
                room["status"] = "finished"
            self.rooms[room_id] = room
            return self.get_room(room_id)

    def add_event(self, payload):
        event = identifier(payload.get("event"), "event")
        game = identifier(payload.get("game_id"), "game_id")
        data = payload.get("data", {})
        if not isinstance(data, dict) or len(json.dumps(data)) > 4096:
            raise ValueError("data must be a small JSON object")
        if event not in {"runtime.ready", "song.selected", "score.observed", "session.ended"}:
            raise ValueError("unsupported event")
        item = {"event": event, "game_id": game, "data": data, "received_at": int(time.time())}
        with self.lock:
            self.events.append(item)
        return {"accepted": True, "count": len(self.events)}

    def list_events(self):
        with self.lock:
            return {"events": list(self.events)}


def build_handler(state: CompanionState, token: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "2EZCompanion/0.1"

        def log_message(self, format, *args):
            # Avoid logging request URLs, which can include client-provided fields.
            pass

        def respond(self, status, result):
            data = json.dumps(result, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def respond_dashboard(self):
            path = Path(__file__).resolve().parent / "dashboard.html"
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'; "
                             "form-action 'self'; base-uri 'none'")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            if token is None:
                return True
            provided = self.headers.get("Authorization", "")
            return hmac.compare_digest(provided, f"Bearer {token}")

        def dispatch(self, method):
            # The dashboard contains no private data. API endpoints remain
            # protected by the optional bearer token supplied in the browser UI.
            route = urlsplit(self.path)
            path = route.path.rstrip("/")
            if method == "GET" and path in {"", "/dashboard"}:
                self.respond_dashboard()
                return
            if not self.authorized():
                self.respond(401, {"error": "authentication required"})
                return
            route = urlsplit(self.path)
            path = route.path.rstrip("/")
            if method == "POST":
                try:
                    length = int(self.headers.get("Content-Length", "-1"))
                    if length < 0 or length > MAX_BODY:
                        self.respond(413, {"error": "invalid request length"})
                        return
                    if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                        self.respond(415, {"error": "Content-Type must be application/json"})
                        return
                    raw = self.rfile.read(length)
                    payload = json.loads(raw.decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("request body must be a JSON object")
                except (UnicodeError, json.JSONDecodeError, ValueError) as error:
                    self.respond(400, {"error": str(error)})
                    return
            else:
                payload = {}
            try:
                parts = path.split("/")
                if method == "GET" and path == "/health":
                    result = {"status": "ok", "name": "2EZConfig companion", "version": "0.1"}
                elif method == "GET" and path == "/api/v1/leaderboard":
                    result = state.leaderboard(parse_qs(route.query))
                elif method == "POST" and path == "/api/v1/scores":
                    result = state.add_score(payload)
                elif method == "GET" and path == "/api/v1/events":
                    result = state.list_events()
                elif method == "POST" and path == "/api/v1/events":
                    result = state.add_event(payload)
                elif method == "GET" and path == "/api/v1/lobbies":
                    result = state.list_rooms()
                elif method == "POST" and path == "/api/v1/lobbies":
                    result = state.create_room(payload)
                elif len(parts) >= 4 and parts[:3] == ["", "api", "v1"] and parts[3] == "lobbies":
                    if len(parts) == 5 and method == "GET":
                        result = state.get_room(parts[4])
                    elif len(parts) == 6 and method == "POST":
                        action = parts[5]
                        actions = {
                            "join": state.join_room,
                            "ready": state.set_ready,
                            "start": state.start_room,
                            "finish": state.submit_room_score,
                        }
                        if action not in actions:
                            self.respond(404, {"error": "unknown endpoint"})
                            return
                        result = actions[action](parts[4], payload)
                    else:
                        self.respond(404, {"error": "unknown endpoint"})
                        return
                else:
                    self.respond(404, {"error": "unknown endpoint"})
                    return
                self.respond(200 if method == "GET" else 201, result)
            except KeyError as error:
                self.respond(404, {"error": str(error)})
            except (ValueError, TypeError) as error:
                self.respond(400, {"error": str(error)})

        def do_GET(self):
            self.dispatch("GET")

        def do_POST(self):
            self.dispatch("POST")

    return Handler


def serve(host="127.0.0.1", port=8765, db="companion-scores.sqlite3", token=None):
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise ValueError("A bearer token is required when binding outside localhost")
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    state = CompanionState(db)
    server = ThreadingHTTPServer((host, port), build_handler(state, token))
    print(f"2EZConfig companion on http://{host}:{server.server_port}; DB={db}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Default: loopback only")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default="companion-scores.sqlite3")
    parser.add_argument("--token", default=None, help="Required when listening on non-loopback")
    args = parser.parse_args()
    serve(args.host, args.port, args.db, args.token)


if __name__ == "__main__":
    main()
