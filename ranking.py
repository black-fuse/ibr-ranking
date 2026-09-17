import json
import os
from collections import defaultdict


class PlayerStats:
    def __init__(self, uuid):
        self.uuid = uuid
        self.name = uuid

        self.performances = 0
        self.tracks = set()

        self.positions = []
        self.times = []

        self.track_records = 0
        self.podiums = 0
        self.top_5 = 0
        self.top_10 = 0

        self.score = 0.0

        self.coverage = 0.0

    @property
    def average_position(self):
        if not self.positions:
            return None

        return sum(self.positions) / len(self.positions)

    @property
    def best_position(self):
        if not self.positions:
            return None

        return min(self.positions)

    @property
    def best_time(self):
        if not self.times:
            return None

        return min(self.times)


class RankingSystem:
    def __init__(self, tracks_path="data/tracks.json",
                 players_path="data/players.json"):

        self.tracks_path = tracks_path
        self.players_path = players_path

        self.tracks = {}
        self.players = {}
        self.stats = {}

        self.load()



    # loading ----------------------------------------------
    def load(self):
        self.load_tracks()
        self.load_players()
        self.calculate_stats()



    def load_tracks(self):
        if not os.path.exists(self.tracks_path):
            raise FileNotFoundError(
                f"Could not find {self.tracks_path}"
            )

        with open(self.tracks_path, "r", encoding="utf-8") as f:
            self.tracks = json.load(f)



    def load_players(self):
        if not os.path.exists(self.players_path):
            print(
                f"[WARN] {self.players_path} not found. "
                "UUIDs will be displayed instead of names."
            )
            return

        try:
            with open(self.players_path, "r", encoding="utf-8") as f:
                self.players = json.load(f)

        except Exception as e:
            print(f"[WARN] Failed to load players.json: {e}")



    # Stats ---------------------------------------
    def calculate_stats(self):
        self.stats = {}

        total_tracks = len(self.tracks)

        for track_id, track in self.tracks.items():

            leaderboard = track.get("leaderboard", [])

            for index, performance in enumerate(leaderboard, start=1):

                uuid = performance.get("player_uuid")

                if not uuid:
                    continue

                if uuid not in self.stats:
                    self.stats[uuid] = PlayerStats(uuid)

                stats = self.stats[uuid]

                # Use saved position if available,
                # otherwise derive it from leaderboard order.
                position = performance.get("position")

                if position is None:
                    position = index

                stats.performances += 1
                stats.tracks.add(track_id)
                stats.positions.append(position)

                time = performance.get("time")

                if time is not None:
                    try:
                        stats.times.append(float(time))
                    except (ValueError, TypeError):
                        pass

                # Track achievements
                if position == 1:
                    stats.track_records += 1

                if position <= 3:
                    stats.podiums += 1

                if position <= 5:
                    stats.top_5 += 1

                if position <= 10:
                    stats.top_10 += 1

        # Calculate coverage
        for stats in self.stats.values():

            stats.coverage = (
                len(stats.tracks) / total_tracks * 100
                if total_tracks
                else 0
            )

        self.calculate_scores()
    # ---------------------------------------------------------
    # Ranking formula
    # ---------------------------------------------------------

    def calculate_scores(self):

        for stats in self.stats.values():

            if stats.performances == 0:
                continue

            # -------------------------------------------------
            # POSITION SCORE
            #
            # 1st  = 100
            # 2nd  = 99
            # ...
            #
            # This is intentionally simple for now.
            # -------------------------------------------------

            position_score = sum(
                max(0, 101 - position)
                for position in stats.positions
            )

            # Average position contribution.
            average_position_score = (
                max(0, 101 - stats.average_position)
            )

            # -------------------------------------------------
            # ACHIEVEMENT SCORE
            # -------------------------------------------------

            track_record_score = stats.track_records * 25
            podium_score = stats.podiums * 10
            top_5_score = stats.top_5 * 3
            top_10_score = stats.top_10 * 1

            # -------------------------------------------------
            # PARTICIPATION
            #
            # Slight reward for actually having a large sample,
            # but not enough to overpower skill.
            # -------------------------------------------------

            participation_score = min(
                stats.performances,
                100
            ) * 0.5

            # -------------------------------------------------
            # FINAL SCORE
            #
            # THIS is the bit you'll probably spend time tuning.
            # -------------------------------------------------

            stats.score = (
                position_score
                + average_position_score * 5
                + track_record_score
                + podium_score
                + top_5_score
                + top_10_score
                + participation_score
            )

    # ---------------------------------------------------------
    # Player lookup
    # ---------------------------------------------------------

    def get_name(self, uuid):

        player = self.players.get(uuid)

        if not player:
            return uuid

        return (
            player.get("display_name")
            or player.get("name")
            or uuid
        )

    def get_stats(self, uuid):

        return self.stats.get(uuid)

    # ---------------------------------------------------------
    # Rankings
    # ---------------------------------------------------------

    def rankings(self, limit=None):

        ranked = sorted(
            self.stats.values(),
            key=lambda x: x.score,
            reverse=True
        )

        if limit:
            return ranked[:limit]

        return ranked

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(self, query):

        query = query.lower()

        results = []

        for uuid, stats in self.stats.items():

            name = self.get_name(uuid)

            if (
                query in uuid.lower()
                or query in name.lower()
            ):
                results.append(stats)

        return sorted(
            results,
            key=lambda x: x.score,
            reverse=True
        )

    # ---------------------------------------------------------
    # Compare
    # ---------------------------------------------------------

    def compare(self, uuid1, uuid2):

        return (
            self.get_stats(uuid1),
            self.get_stats(uuid2)
        )

    # ---------------------------------------------------------
    # Track information
    # ---------------------------------------------------------

    def get_track(self, track_id):

        # JSON keys are strings.
        return self.tracks.get(str(track_id))

    # ---------------------------------------------------------
    # Leaderboard position
    # ---------------------------------------------------------

    def get_rank(self, uuid):

        ranked = self.rankings()

        for position, stats in enumerate(ranked, start=1):

            if stats.uuid == uuid:
                return position

        return None