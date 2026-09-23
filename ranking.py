import json
import requests
import os
from collections import defaultdict
from tqdm import tqdm


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
    def __init__(
        self,
        tracks_path="data/tracks.json",
        players_path="data/players.json",
        source=None
    ):
        self.tracks_path = tracks_path
        self.players_path = players_path
        self.source = source

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

        # Only tracks belonging to this ranking
        ranking_tracks = {
            track_id: track
            for track_id, track in self.tracks.items()
            if self.source is None or track.get("source") == self.source
        }

        total_tracks = len(ranking_tracks)

        for track_id, track in ranking_tracks.items():

            leaderboard = track.get("leaderboard", [])

            for index, performance in enumerate(leaderboard, start=1):

                uuid = performance.get("player_uuid")

                if not uuid:
                    continue

                if uuid not in self.stats:
                    self.stats[uuid] = PlayerStats(uuid)

                stats = self.stats[uuid]

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

                if position == 1:
                    stats.track_records += 1

                if position <= 3:
                    stats.podiums += 1

                if position <= 5:
                    stats.top_5 += 1

                if position <= 10:
                    stats.top_10 += 1

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
            try:
                response = requests.get(
                    f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}",
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                return data["name"]

            except Exception as e:
                print(f"[WARN] {e}")
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

    def export_json(
        self,
        output_path="website/data/rankings.json",
        page_size=1000
    ):

        # Turn the requested file path into a directory.
        # rankings.json -> rankings/
        output_dir = os.path.splitext(output_path)[0]

        os.makedirs(output_dir, exist_ok=True)

        rankings = self.rankings()

        total_players = len(rankings)
        total_pages = (
            (total_players + page_size - 1) // page_size
            if total_players
            else 0
        )

        # ---------------------------------------------------------
        # Export ranking pages
        # ---------------------------------------------------------

        # ---------------------------------------------------------
        # Export ranking pages
        # ---------------------------------------------------------

        progress = tqdm(
            total=total_players,
            desc="Exporting rankings",
            unit="player"
        )

        for page in range(total_pages):

            start = page * page_size
            end = min(start + page_size, total_players)

            page_rankings = rankings[start:end]

            data = []

            for rank, stats in enumerate(
                page_rankings,
                start=start + 1
            ):

                data.append({
                    "rank": rank,
                    "uuid": stats.uuid,
                    "name": self.get_name(stats.uuid),

                    "score": round(stats.score, 2),

                    "performances": stats.performances,
                    "tracks": len(stats.tracks),
                    "coverage": round(stats.coverage, 2),

                    "track_records": stats.track_records,
                    "podiums": stats.podiums,
                    "top_5": stats.top_5,
                    "top_10": stats.top_10,

                    "average_position": (
                        round(stats.average_position, 2)
                        if stats.average_position is not None
                        else None
                    ),

                    "best_position": stats.best_position,

                    "best_time": (
                        round(stats.best_time, 3)
                        if stats.best_time is not None
                        else None
                    )
                })

                progress.update(1)

            page_path = os.path.join(
                output_dir,
                f"page_{page + 1}.json"
            )

            with open(
                page_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    separators=(",", ":")
                )

        progress.close()

        # ---------------------------------------------------------
        # Export metadata
        # ---------------------------------------------------------

        metadata = {
            "total_players": total_players,
            "page_size": page_size,
            "total_pages": total_pages
        }

        metadata_path = os.path.join(
            output_dir,
            "index.json"
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        print(
            f"[INFO] Exported {total_players} players "
            f"across {total_pages} pages to {output_dir}"
        )

ranking = RankingSystem()

ranking.export_json()

frosthex_ranking = RankingSystem(source="frosthex")
frosthex_ranking.export_json(
    "website/data/rankings_frosthex.json"
)

frosthex_event_ranking = RankingSystem(source="frosthexEvent")
frosthex_event_ranking.export_json(
    "website/data/rankings_frosthexEvent.json"
)


brwc_ranking = RankingSystem(source="brwc")
brwc_ranking.export_json(
    "website/data/rankings_brwc.json"
)

bbrl_ranking = RankingSystem(source="bbrl")
bbrl_ranking.export_json(
    "website/data/rankings_bbrl.json"
)

boatlabs_ranking = RankingSystem(source="boatlabs")
boatlabs_ranking.export_json(
    "website/data/rankings_boatlabs.json"
)

wolfnetwork_ranking = RankingSystem(source="wolfnetwork")
wolfnetwork_ranking.export_json(
    "website/data/rankings_wolfnetwork.json"
)