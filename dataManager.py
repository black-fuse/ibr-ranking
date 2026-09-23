import json
import os

import sources.frosthexEvent as frosthexEvent
import sources.frosthex as frosthex
import sources.brwc as brwc
import sources.bbrl as bbrl
import sources.boatlabs as boatlabs

from models import Track, Player

from tqdm import tqdm


class DataManager:

    def __init__(self):

        # All data sources
        self.sources = [
            ("frosthex", frosthex),
            ("frosthexEvent", frosthexEvent),
            ("brwc", brwc),
            ("bbrl", bbrl),
            ("boatlabs", boatlabs)
        ]

        self.tracks = {}
        self.players = {}

        self.failed_tracks = []
        self.failed_players = []


    def load_cache(self):

        # Players
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


        # Tracks
        if os.path.exists("data/tracks.json"):
            try:
                with open("data/tracks.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                for track_id, track_data in data.items():
                    try:
                        track = Track.from_dict(track_data)
                        self.tracks[track.internal_id] = track

                    except Exception as e:
                        print(
                            "[WARN] Failed to load cached track "
                            f"{track_id}: {e}"
                        )

                print(f"Loaded {len(self.tracks)} tracks from cache.")

            except Exception as e:
                print(f"[WARN] Failed to load tracks cache: {e}")


    # =========================================================
    # TRACKS
    # =========================================================

    def load_tracks(self):

        for source_name, source in self.sources:

            print(f"\n--- Loading tracks from {source_name} ---")

            try:
                tracklist = source.get_tracks()
                track_names = tracklist["track_command_names"]

            except Exception as e:
                print(
                    f"[ERROR] Failed to retrieve {source_name} "
                    f"track list: {e}"
                )
                continue

            print(
                f"{source_name} currently has "
                f"{len(track_names)} tracks."
            )

            # Tracks already cached from this source
            cached_commands = {
                track.command_name
                for track in self.tracks.values()
                if track.source == source_name
            }

            new_tracks = [
                command_name
                for command_name in track_names
                if command_name not in cached_commands
            ]

            print(f"Cached tracks: {len(cached_commands)}")
            print(f"New tracks: {len(new_tracks)}")

            if not new_tracks:
                print("No new tracks to load.")
                continue

            # Download new tracks
            for command_name in tqdm(
                new_tracks,
                desc=f"Loading {source_name} tracks",
                unit="track"
            ):

                try:
                    data = source.get_track(command_name)

                    track = Track(data, source_name)

                    if track.open == False:
                        print(f"[Log] Skipped {track.display_name} because it was closed")

                        self.failed_tracks.append({
                                                "source": source_name,
                                                "command_name": command_name,
                                                "error": "track was closed"
                                            })
                        
                    else:
                        self.tracks[track.internal_id] = track

                except Exception as e:
                    print(
                        f"\n[WARN] Failed to load "
                        f"{source_name} track "
                        f"{command_name}: {e}"
                    )

                    self.failed_tracks.append({
                        "source": source_name,
                        "command_name": command_name,
                        "error": str(e)
                    })

        print(f"\nTotal tracks: {len(self.tracks)}")
        print(f"Failed tracks: {len(self.failed_tracks)}")


    # =========================================================
    # PLAYERS
    # =========================================================

    def load_missing_players(self):

        # UUID -> source
        player_sources = {}

        # Find every player referenced by our tracks
        for track in self.tracks.values():

            try:
                for performance in track.leaderboard:

                    uuid = performance.player_uuid

                    # Remember where we found this player
                    if uuid not in player_sources:
                        player_sources[uuid] = track.source

            except Exception as e:

                print(
                    f"\n[WARN] Failed to read leaderboard "
                    f"for track {track.id}: {e}"
                )

        # Compare against cache
        missing_players = [
            uuid
            for uuid in player_sources
            if uuid not in self.players
        ]

        print(
            f"Players referenced by tracks: "
            f"{len(player_sources)}"
        )

        print(
            f"Players already cached: "
            f"{len(self.players)}"
        )

        print(
            f"Players missing: "
            f"{len(missing_players)}"
        )

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
                source_name = player_sources[uuid]

                self.get_or_create_player(
                    uuid,
                    source_name
                )

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

    def get_or_create_player(self, uuid, source_name):

        if uuid in self.players:
            return self.players[uuid]

        # Find the requested source
        source = dict(self.sources)[source_name]

        data = source.get_player(uuid)

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
            print(
                f"[ERROR] Failed to create data directory: {e}"
            )
            return


        # Tracks
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


        # Players
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


        # Errors
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


    # =========================================================
    # JSON
    # =========================================================

    def save_json(self, path, data):

        temp_path = path + ".tmp"

        try:

            with open(
                temp_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=4
                )

            if os.path.exists(path):
                os.replace(
                    path,
                    path + ".bak"
                )

            os.replace(
                temp_path,
                path
            )

        except Exception:

            if os.path.exists(temp_path):
                os.remove(temp_path)

            raise