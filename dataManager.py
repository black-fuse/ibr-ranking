import json
import os

import sources.frosthex.frosthex as frosthex
from models import Track, Player

from tqdm import tqdm


class DataManager:

    def __init__(self):
        self.tracks = {}
        self.players = {}

        self.failed_tracks = []
        self.failed_players = []

    # =========================================================
    # CACHE LOADING
    # =========================================================

    def load_cache(self):
        """
        Load existing cached data from disk.
        """

        # -------------------------
        # Players
        # -------------------------

        if os.path.exists("data/players.json"):
            try:
                with open("data/players.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                for uuid, player_data in data.items():
                    try:
                        self.players[uuid] = Player.from_dict(player_data)
                    except Exception as e:
                        print(
                            f"[WARN] Failed to load cached player "
                            f"{uuid}: {e}"
                        )

                print(f"Loaded {len(self.players)} players from cache.")

            except Exception as e:
                print(f"[WARN] Failed to load players cache: {e}")

        else:
            print("No player cache found.")

        # -------------------------
        # Tracks
        # -------------------------

        if os.path.exists("data/tracks.json"):
            try:
                with open("data/tracks.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                for track_id, track_data in data.items():
                    try:
                        track = Track.from_dict(track_data)
                        self.tracks[track.id] = track

                    except Exception as e:
                        print(
                            f"[WARN] Failed to load cached track "
                            f"{track_id}: {e}"
                        )

                print(f"Loaded {len(self.tracks)} tracks from cache.")

            except Exception as e:
                print(f"[WARN] Failed to load tracks cache: {e}")

    # =========================================================
    # TRACKS
    # =========================================================

    def load_tracks(self):

        # Get current track list
        try:
            tracklist = frosthex.get_tracks()
            track_names = tracklist["track_command_names"]

        except Exception as e:
            print(f"[ERROR] Failed to retrieve track list: {e}")
            return

        print(f"Frosthex currently has {len(track_names)} tracks.")

        # Figure out which tracks we already have
        cached_commands = {
            track.command_name
            for track in self.tracks.values()
            if track.source == "frosthex"
        }

        new_tracks = [
            command_name
            for command_name in track_names
            if command_name not in cached_commands
        ]

        print(f"Cached tracks: {len(cached_commands)}")
        print(f"New tracks: {len(new_tracks)}")

        # Nothing to download
        if not new_tracks:
            print("No new tracks to load.")

        # Download new tracks
        for command_name in tqdm(
            new_tracks,
            desc="Loading new tracks",
            unit="track"
        ):
            try:
                data = frosthex.get_track(command_name)

                track = Track(data, "frosthex")

                self.tracks[track.id] = track

            except Exception as e:
                print(
                    f"\n[WARN] Failed to load track "
                    f"{command_name}: {e}"
                )

                self.failed_tracks.append({
                    "command_name": command_name,
                    "error": str(e)
                })

        print(f"\nTotal tracks: {len(self.tracks)}")
        print(f"Failed tracks: {len(self.failed_tracks)}")

    # =========================================================
    # PLAYERS
    # =========================================================

    def load_missing_players(self):

        # Find every player referenced by our tracks
        player_uuids = set()

        for track in self.tracks.values():
            try:
                for performance in track.leaderboard:
                    player_uuids.add(performance.player_uuid)

            except Exception as e:
                print(
                    f"\n[WARN] Failed to read leaderboard "
                    f"for track {track.id}: {e}"
                )

        # Compare against cache
        missing_players = [
            uuid
            for uuid in player_uuids
            if uuid not in self.players
        ]

        print(f"Players referenced by tracks: {len(player_uuids)}")
        print(f"Players already cached: {len(self.players)}")
        print(f"Players missing: {len(missing_players)}")

        # Nothing to download
        if not missing_players:
            print("All required players are already cached.")
            return

        # Fetch missing players
        for uuid in tqdm(
            missing_players,
            desc="Loading missing players",
            unit="player"
        ):
            try:
                self.get_or_create_player(uuid)

            except Exception as e:
                print(
                    f"\n[WARN] Failed to load player "
                    f"{uuid}: {e}"
                )

                self.failed_players.append({
                    "uuid": uuid,
                    "error": str(e)
                })

        print(f"\nTotal players: {len(self.players)}")
        print(f"Failed players: {len(self.failed_players)}")

    # =========================================================
    # PLAYER FETCHING
    # =========================================================

    def get_or_create_player(self, uuid):

        if uuid in self.players:
            return self.players[uuid]

        data = frosthex.get_player(uuid)

        player = Player(data)

        self.players[uuid] = player

        return player

    # =========================================================
    # SAVE
    # =========================================================

    def save(self):

        try:
            os.makedirs("data", exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Failed to create data directory: {e}")
            return

        # -------------------------
        # Tracks
        # -------------------------

        try:
            self.save_json(
                "data/tracks.json",
                {
                    str(track_id): track.to_dict()
                    for track_id, track in self.tracks.items()
                }
            )

            print(f"Saved {len(self.tracks)} tracks.")

        except Exception as e:
            print(f"[ERROR] Failed to save tracks: {e}")

        # -------------------------
        # Players
        # -------------------------

        try:
            self.save_json(
                "data/players.json",
                {
                    uuid: player.to_dict()
                    for uuid, player in self.players.items()
                }
            )

            print(f"Saved {len(self.players)} players.")

        except Exception as e:
            print(f"[ERROR] Failed to save players: {e}")

        # -------------------------
        # Errors
        # -------------------------

        try:
            self.save_json(
                "data/import_errors.json",
                {
                    "tracks": self.failed_tracks,
                    "players": self.failed_players
                }
            )

        except Exception as e:
            print(
                f"[WARN] Failed to save import errors: {e}"
            )

    # =========================================================
    # FULL IMPORT
    # =========================================================

    def update(self):

        print("========================================")
        print(" Loading cached data")
        print("========================================")

        self.load_cache()

        print("\n========================================")
        print(" Updating tracks")
        print("========================================")

        self.load_tracks()

        print("\n========================================")
        print(" Updating players")
        print("========================================")

        self.load_missing_players()

        print("\n========================================")
        print(" Saving")
        print("========================================")

        self.save()


    def save_json(self, path, data):
        temp_path = path + ".tmp"

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            if os.path.exists(path):
                os.replace(path, path + ".bak")

            os.replace(temp_path, path)

        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)

            raise