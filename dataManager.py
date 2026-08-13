import json
import os

import sources.frosthex.frosthex as frosthex
from models import Track, Player


class DataManager:

    def __init__(self):
        self.tracks = {}
        self.players = {}

    def load_tracks(self):
        tracklist = frosthex.get_tracks()

        for command_name in tracklist["track_command_names"]:
            data = frosthex.get_track(command_name)

            track = Track(data)

            self.tracks[track.id] = track

            # Add players encountered in leaderboard
            for performance in track.leaderboard:
                self.get_or_create_player(performance.player_uuid)

    def get_or_create_player(self, uuid):
        if uuid in self.players:
            return self.players[uuid]

        data = frosthex.get_player(uuid)

        player = Player(data)

        self.players[uuid] = player

        return player

    def save(self):
        os.makedirs("data", exist_ok=True)

        with open("data/tracks.json", "w") as f:
            json.dump(
                {
                    str(track_id): track.to_dict()
                    for track_id, track in self.tracks.items()
                },
                f,
                indent=4
            )

        with open("data/players.json", "w") as f:
            json.dump(
                {
                    uuid: player.to_dict()
                    for uuid, player in self.players.items()
                },
                f,
                indent=4
            )