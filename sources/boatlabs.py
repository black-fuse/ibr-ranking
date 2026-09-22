import requests
import json
import os

BASE_URL = "https://api.boatlabs.net/v1/timingsystems"
PLAYER_URL = "https://boatlabs.net/api/player"

_player_uuid_cache = {}
_player_name_cache = {}

def username_to_uuid(username):
    username_key = username.lower()

    # Check cached players first
    if username_key in _player_name_cache:
        return _player_name_cache[username_key]

    # Not cached, ask Mojang
    try:
        response = requests.get(
            f"https://api.mojang.com/users/profiles/minecraft/{username}",
            timeout=10
        )

        if response.status_code == 204:
            print(f"[WARN] Mojang could not find player {username}")
            return None

        response.raise_for_status()

        data = response.json()

        raw_uuid = data["id"]

        # Convert Mojang's undashed UUID into the format
        uuid = (
            f"{raw_uuid[:8]}-{raw_uuid[8:12]}-"
            f"{raw_uuid[12:16]}-{raw_uuid[16:20]}-"
            f"{raw_uuid[20:]}"
        )

        # Cache it for the rest of this import
        _player_name_cache[username_key] = uuid
        _player_uuid_cache[uuid] = {
            "uuid": uuid,
            "name": username
        }

        return uuid

    except Exception as e:
        print(
            f"[WARN] Failed to resolve player "
            f"{username}: {e}"
        )
        return None


def get_tracks():
    response = requests.get(
        f"{BASE_URL}/getTracks",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    return {
        "track_command_names": [
            track["command_name"]
            for track in data["tracks"]
        ]
    }

def get_track(track_name):

    response = requests.get(
        f"{BASE_URL}/getTrack/{track_name}",
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    normalized_top_list = []

    for performance in data.get("top_list", []):

        username = performance["name"]

        uuid = username_to_uuid(username)

        if uuid is None:
            continue

        normalized_top_list.append({
            "player_uuid": uuid,
            "time": performance["time"],
            "date": None
        })

    data["top_list"] = normalized_top_list

    return data

def get_player(uuid):
    if uuid in _player_uuid_cache:
        return _player_uuid_cache[uuid]

    response = requests.get(
        f"{PLAYER_URL}/{uuid}",
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    player = {
        "uuid": data["uuid"],
        "name": data["username"]
    }

    _player_uuid_cache[uuid] = player

    return player


def getEvents():
    response = requests.get(
            f"{BASE_URL}/getEvents",
            timeout=10
        )

    response.raise_for_status()
    return response.json()

def getEvent(event_name):
    response = requests.get(
            f"{BASE_URL}/getEvent{event_name}",
            timeout=10
        )

    response.raise_for_status()
    return response.json()