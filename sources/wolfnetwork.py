import hashlib
from urllib.parse import quote

import requests


BASE_URL = "http://143.14.179.72:10003/api/v1"

_player_cache = {}


def get_tracks():
    response = requests.get(
        f"{BASE_URL}/readonly/tracks",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    return {
        "track_command_names": [
            track["name"]
            for track in data["tracks"]
        ]
    }


def get_player(uuid):
    response = requests.get(
        f"{BASE_URL}/readonly/players/{quote(uuid, safe='')}",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    return {
        "uuid": data["uuid"],
        "name": data["name"]
    }


def username_to_uuid(username):
    key = username.lower()

    if key in _player_cache:
        return _player_cache[key]

    response = requests.get(
        f"{BASE_URL}/readonly/players/{quote(username, safe='')}",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    uuid = data["uuid"]

    _player_cache[key] = uuid

    return uuid


def make_track_id(track_name):
    digest = hashlib.sha256(
        track_name.encode("utf-8")
    ).digest()

    return int.from_bytes(digest[:4], "big")


def get_track(track_name):
    encoded_name = quote(track_name, safe="")

    # Get track metadata
    response = requests.get(
        f"{BASE_URL}/readonly/tracks/{encoded_name}",
        timeout=10
    )
    response.raise_for_status()

    track = response.json()

    # Get all stored times
    response = requests.get(
        f"{BASE_URL}/readonly/tracks/{encoded_name}/times",
        timeout=10
    )
    response.raise_for_status()

    times = response.json()

    leaderboard = []

    for performance in times.get("times", []):
        # Ignore unfinished runs
        if not performance.get("finished", False):
            continue

        uuid = username_to_uuid(
            performance["player_name"]
        )

        leaderboard.append({
            "player_uuid": uuid,
            "time": performance["time_ms"],
            "date": performance.get("date")
        })

    return {
        "id": make_track_id(track["name"]),

        "command_name": track["name"],
        "display_name": track["name"],

        "type": "Boat",
        "open": True,

        "date_created": None,

        "total_attempts": 0,
        "total_finishes": len(leaderboard),
        "total_time_spent": 0,

        "weight": 100,

        "options": [],

        "owner": track.get("creator"),

        "spawn_location": track.get("spawn"),

        "tags": [],

        "medals": track.get("medals", {}),

        "top_list": leaderboard
    }