import json
import os

import sources.frosthexEvent as frosthexEvent
import sources.frosthex as frosthex
import sources.brwc as brwc
import sources.bbrl as bbrl
import sources.boatlabs as boatlabs
import sources.wolfnetwork as wolfnetwork

from models import Track, Player, Event

import requests
from urllib.parse import quote
from tqdm import tqdm


class DataManager:

    def __init__(self):

        # All data sources
        self.sources = [
            ("frosthex", frosthex),
            ("frosthexEvent", frosthexEvent),
            ("brwc", brwc),
            ("bbrl", bbrl),
            ("wolfnetwork", wolfnetwork),
            ("boatlabs", boatlabs)
        ]

        self.tracks = {}
        self.players = {}
        self.events = {}

        self.failed_tracks = []
        self.failed_players = []
        self.failed_events = []


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


        # Events
        if os.path.exists("data/events.json"):
            try:
                with open("data/events.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                for internal_id, event_data in data.items():
                    try:
                        event = Event.from_dict(event_data)
                        self.events[event.internal_id] = event

                    except Exception as e:
                        print(
                            f"[WARN] Failed to load cached event "
                            f"{internal_id}: {e}"
                        )

                print(f"Loaded {len(self.events)} events from cache.")

            except Exception as e:
                print(f"[WARN] Failed to load events cache: {e}")
        else:
            print("No events cache found.")


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
    # EVENTS
    # =========================================================
    def get_event_list(self, source_name, source):
        """Retrieve the event listing for a supported source."""

        if source_name == "boatlabs":
            response = requests.get(
                f"{source.BASE_URL}/getEvents",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("events", [])

        elif source_name == "wolfnetwork":
            response = requests.get(
                f"{source.BASE_URL}/readonly/events",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("events", [])

        # The other sources are not currently supported for event imports.
        return []


    def get_event_details(self, source_name, source, event_data):
        """Retrieve the full details for one event."""

        if source_name == "boatlabs":
            event_name = event_data["name"]
            url = (
                f"{source.BASE_URL}/getEvent/"
                f"{quote(str(event_name), safe='')}"
            )

        elif source_name == "wolfnetwork":
            event_name = event_data["name"]
            url = (
                f"{source.BASE_URL}/readonly/events/results/"
                f"{quote(str(event_name), safe='')}"
            )

        else:
            raise ValueError(
                f"Event imports are not supported for {source_name}"
            )

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()


    def load_events(self):
        """Load new events from supported sources into the event cache."""

        if not hasattr(self, "events"):
            self.events = {}

        if not hasattr(self, "failed_events"):
            self.failed_events = []

        for source_name, source in self.sources:
            print(f"\n--- Loading events from {source_name} ---")

            try:
                event_list = self.get_event_list(source_name, source)

            except Exception as e:
                print(
                    f"[ERROR] Failed to retrieve {source_name} "
                    f"event list: {e}"
                )

                self.failed_events.append({
                    "source": source_name,
                    "event": None,
                    "error": str(e),
                })
                continue

            print(f"{source_name} currently has {len(event_list)} events.")

            # Use source-prefixed identifiers to avoid collisions between APIs.
            cached_ids = {
                event.internal_id
                for event in self.events.values()
                if event.source == source_name
            }

            new_events = []

            for event_data in event_list:
                event_id = event_data.get("id")
                event_name = event_data.get("name")

                # Prefer the source ID where available, otherwise use the name.
                identifier = (
                    str(event_id)
                    if event_id is not None
                    else str(event_name)
                )

                internal_id = f"{source_name}:{identifier}"

                if internal_id not in cached_ids:
                    new_events.append(event_data)

            print(f"Cached events: {len(cached_ids)}")
            print(f"New events: {len(new_events)}")

            if not new_events:
                print("No new events to load.")
                continue

            for event_data in tqdm(
                new_events,
                desc=f"Loading {source_name} events",
                unit="event",
            ):
                event_name = event_data.get(
                    "name",
                    str(event_data.get("id", "unknown")),
                )

                try:
                    details = self.get_event_details(
                        source_name,
                        source,
                        event_data,
                    )

                    # Some APIs may omit their ID in the detailed response.
                    # Retain the listing's ID if that happens.
                    if details.get("id") is None and event_data.get("id") is not None:
                        details["id"] = event_data["id"]

                    if not details.get("name"):
                        details["name"] = event_name

                    event = Event(details, source_name)

                    self.events[event.internal_id] = event
                    cached_ids.add(event.internal_id)

                except Exception as e:
                    print(
                        f"\n[WARN] Failed to load {source_name} "
                        f"event {event_name}: {e}"
                    )

                    self.failed_events.append({
                        "source": source_name,
                        "event": event_name,
                        "error": str(e),
                    })

        print(f"\nTotal events: {len(self.events)}")
        print(f"Failed events: {len(self.failed_events)}")


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


        # Events
        try:
            self.save_json(
                "data/events.json",
                {
                    internal_id: event.to_dict()
                    for internal_id, event in self.events.items()
                }
            )
            print(f"Saved {len(self.events)} events.")

        except Exception as e:
            print(f"[ERROR] Failed to save events: {e}")


        # Errors
        try:
            self.save_json(
                "data/import_errors.json",
                {
                    "tracks": self.failed_tracks,
                    "players": self.failed_players,
                    "events": self.failed_events
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
        try:
            print("Loading cached data")
            self.load_cache()

            print("Updating tracks")
            self.load_tracks()

            print("Updating events")
            self.load_events()

            print("Updating players")
            self.load_missing_players()

        except KeyboardInterrupt:
            print("\n[INFO] Import interrupted. Saving progress...")

        finally:
            print("\nSaving data...")
            self.save()
            print("Done.")


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