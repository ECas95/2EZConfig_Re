#!/usr/bin/env python3
"""Review a local 2ez-events.jsonl spool and optionally relay opt-in events.

Run on a modern PC, not necessarily on the XP cabinet. Default is DRY RUN.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def parse_line(line):
    record = json.loads(line)
    if not isinstance(record, dict) or record.get("schema_version") != 1:
        raise ValueError("record must be a v1 JSON object")
    for key in ("event", "game_id"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValueError(f"missing {key}")
    data = record.get("data", {})
    if not isinstance(data, dict):
        raise ValueError("data must be an object")
    return {"event": record["event"], "game_id": record["game_id"], "data": data}


def validate_destination(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("server must be an http(s) URL")
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("refusing plaintext HTTP to a remote host; use HTTPS via a trusted reverse proxy")
    return url.rstrip("/") + "/api/v1/events"


def run(file_path, server, token, send=False, limit=100):
    target = validate_destination(server)
    if not 1 <= limit <= 10000:
        raise ValueError("--limit must be 1..10000")
    seen = 0
    sent = 0
    with Path(file_path).open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = parse_line(line)
            seen += 1
            if seen > limit:
                break
            print(f"{lineno}: {record['game_id']} {record['event']}")
            if not send:
                continue
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            request = Request(target, data=json.dumps(record).encode("utf-8"),
                              headers=headers, method="POST")
            with urlopen(request, timeout=5) as response:
                if response.status != 201:
                    raise RuntimeError(f"event rejected at line {lineno}")
            sent += 1
    print(f"Processed {min(seen, limit)} events; sent {sent}. "
          + ("No requests made (dry run)." if not send else "Replay is not deduplicated."))
    return sent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="2ez-events.jsonl", help="Local/shared JSONL path")
    parser.add_argument("--server", default="http://127.0.0.1:8765")
    parser.add_argument("--token", default=os.environ.get("EZ2_COMPANION_TOKEN"))
    parser.add_argument("--send", action="store_true",
                        help="Explicit opt-in to POST events; default is dry-run")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    try:
        run(args.file, args.server, args.token, args.send, args.limit)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
