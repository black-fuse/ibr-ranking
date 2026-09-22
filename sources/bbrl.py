import requests

with open(r'sensitives\bbrl.txt') as FHkey:
    API_KEY = FHkey.readline().strip()

BASE_URL = "http://202.36.95.48:27755/api/v1"
V2_URL = "http://202.36.95.48:27755/api/v2"

PARAMS = {
    "api_key": API_KEY
}


def get_tracks():
    response = requests.get(
        f"{BASE_URL}/readonly/tracks",
        params=PARAMS,
    )

    response.raise_for_status()
    return response.json()


def get_track(track_name):
    response = requests.get(
        f"{V2_URL}/readonly/tracks/{track_name}",
        params=PARAMS,
        timeout=10
    )

    response.raise_for_status()
    return response.json()

def get_player(uuid):
    response = requests.get(
        f"{BASE_URL}/readonly/players/{uuid}",
        params=PARAMS,
        timeout=10
    )

    response.raise_for_status()
    return response.json()