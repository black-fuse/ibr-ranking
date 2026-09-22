import requests

BASE_URL = "https://api.boatlabs.net/v1/timingsystems/"
"https://boatlabs.net/api/player/97434c2f-c547-4899-9322-13f75be07920"

def get_tracks():
    response = requests.get(
        f"{BASE_URL}/getTracks"
    )

    response.raise_for_status()
    return response.json()

def get_track(track_name):
    response = requests.get(
    f"{BASE_URL}/getTrack/{track_name}"
    )

    response.raise_for_status()
    return response.json()

def get_player(uuid):
    response = requests.get(
        f"https://boatlabs.net/api/player/{uuid}"
    )

    response.raise_for_status()
    return response.json()

def getEvents():
    response = requests.get(
            f"{BASE_URL}/getEvents"
        )

    response.raise_for_status()
    return response.json()

def getEvent(event_name):
    response = requests.get(
            f"{BASE_URL}/getEvent{event_name}"
        )

    response.raise_for_status()
    return response.json()