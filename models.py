
SOURCE_OFFSETS = {
    "frosthex": 0,
    "frosthexEvent": 1000000,
    "boatlabs": 2000000,
    "brwc": 3000000,
    "bbrl": 4000000,
    "wolfnetwork": 5000000,

}

def make_internal_id(source, source_id):
    return SOURCE_OFFSETS[source] + source_id

class Player:
    def __init__(self, data):
        self.uuid = data["uuid"]
        self.name = data["name"]
        self.display_name = data.get("display_name")
        self.color_code = data.get("color_code")
        self.boat_type = data.get("boat_type")
        self.boat_material = data.get("boat_material")
        self.bukkit_color = data.get("bukkit_color")
        self.hex_color = data.get("hex_color")

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "display_name": self.display_name,
            "color_code": self.color_code,
            "hex_color": self.hex_color,
            "boat_type": self.boat_type,
            "boat_material": self.boat_material,
            "bukkit_color": self.bukkit_color
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data)


class Performance:
    def __init__(self, data, track_id):
        self.player_uuid = data["player_uuid"]
        self.track_id = track_id
        self.time = data["time"]
        self.date = data.get("date")
        self.position = data.get("position")

    def to_dict(self):
        return {
            "player_uuid": self.player_uuid,
            "track_id": self.track_id,
            "time": self.time,
            "date": self.date,
            "position": self.position
        }

    @classmethod
    def from_dict(cls, data):
        performance = cls.__new__(cls)

        performance.player_uuid = data["player_uuid"]
        performance.track_id = data["track_id"]
        performance.time = data["time"]
        performance.date = data["date"]
        performance.position = data["position"]

        return performance

class Track:
    def __init__(self, data, source):
        self.id = data["id"]
        self.internal_id = make_internal_id(
            source,
            self.id
        )

        self.source = source
        self.command_name = data["command_name"]
        self.display_name = data["display_name"]
        self.type = data["type"]

        self.open = data["open"]
        self.date_created = data["date_created"]

        self.attempts = data["total_attempts"]
        self.finishes = data["total_finishes"]
        self.time_spent = data["total_time_spent"]
        self.weight = data["weight"]

        self.options = data.get("options", [])
        self.owner = data.get("owner")
        self.spawn_location = data.get("spawn_location")
        self.tags = data.get("tags", [])
        self.medals = data.get("medals", {})

        self.leaderboard = [
            Performance(performance, self.id)
            for performance in data.get("top_list", [])
        ]

        # Position is easy to derive because top_list is already sorted
        for position, performance in enumerate(self.leaderboard, start=1):
            performance.position = position

    def to_dict(self):
        return {
            "source": self.source,
            "id": self.id,
            "command_name": self.command_name,
            "display_name": self.display_name,
            "type": self.type,
            "attempts": self.attempts,
            "finishes": self.finishes,
            "time_spent": self.time_spent,
            "weight": self.weight,
            "leaderboard": [
                performance.to_dict()
                for performance in self.leaderboard
            ]
        }

    @classmethod
    def from_dict(cls, data):
        track = cls.__new__(cls)

        track.source = data["source"]
        track.id = data["id"]
        track.internal_id = make_internal_id(
            track.source,
            track.id
        )

        track.command_name = data["command_name"]
        track.display_name = data["display_name"]
        track.type = data["type"]
        track.attempts = data["attempts"]
        track.finishes = data["finishes"]
        track.time_spent = data["time_spent"]
        track.weight = data["weight"]

        track.leaderboard = [
            Performance.from_dict(performance)
            for performance in data.get("leaderboard", [])
        ]

        return track


class Event:
    def __init__(self, data, source):
        self.source = source
        self.id = data.get("id")
        self.name = data.get("name") or str(self.id or "unknown")
        self.internal_id = f"{source}:{self.id if self.id is not None else self.name}"

        self.date = data.get("date", data.get("start_time"))
        self.state = data.get("state")
        self.track = data.get("track", data.get("track_name"))

        self.rounds = [
            Round(round_data, self)
            for round_data in data.get("rounds", [])
        ]

    def to_dict(self):
        return {
            "source": self.source,
            "id": self.id,
            "internal_id": self.internal_id,
            "name": self.name,
            "date": self.date,
            "state": self.state,
            "track": self.track,
            "rounds": [round_obj.to_dict() for round_obj in self.rounds],
        }

    @classmethod
    def from_dict(cls, data):
        event = cls(data, data["source"])
        event.rounds = [
            Round.from_dict(round_data, event)
            for round_data in data.get("rounds", [])
        ]
        return event


class Round:
    def __init__(self, data, event):
        self.event = event
        self.name = data.get("name", "Unknown round")
        self.type = data.get("type")
        self.state = data.get("state")
        self.track = data.get("track", data.get("track_name"))

        self.heats = [
            Heat(heat_data, self)
            for heat_data in data.get("heats", [])
        ]

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "state": self.state,
            "track": self.track,
            "heats": [heat.to_dict() for heat in self.heats],
        }

    @classmethod
    def from_dict(cls, data, event):
        round_obj = cls(data, event)
        round_obj.heats = [
            Heat.from_dict(heat_data, round_obj)
            for heat_data in data.get("heats", [])
        ]
        return round_obj


class Heat:
    def __init__(self, data, round_obj):
        self.round = round_obj
        self.name = data.get("name", data.get("id", "Unknown heat"))
        self.laps = data.get("laps")

        result_data = (
            data.get("driver_results")
            or data.get("driver_details")
            or data.get("results")
            or []
        )

        self.driver_results = [
            DriverResult(result, self)
            for result in result_data
        ]

        self.pits = {
            result.uuid: result.pits
            for result in self.driver_results
            if result.pits
        }

    def to_dict(self):
        return {
            "name": self.name,
            "laps": self.laps,
            "driver_results": [
                result.to_dict() for result in self.driver_results
            ],
            "pits": self.pits,
        }

    @classmethod
    def from_dict(cls, data, round_obj):
        heat = cls(data, round_obj)
        heat.driver_results = [
            DriverResult.from_dict(result_data, heat)
            for result_data in data.get("driver_results", [])
        ]
        heat.pits = data.get(
            "pits",
            {
                result.uuid: result.pits
                for result in heat.driver_results
                if result.pits
            },
        )
        return heat


class DriverResult:
    def __init__(self, data, heat):
        self.heat = heat
        self.uuid = data.get("uuid")
        self.name = data.get("name", "Unknown")

        self.start_position = data.get("start_position")
        self.position = data.get("position")

        if "finished" in data:
            self.finished = data["finished"]
        elif data.get("finish_time") is not None:
            self.finished = True
        elif data.get("dnf") is True:
            self.finished = False
        else:
            self.finished = None

        self.dnf = data.get("dnf")

        self.laps = []
        for lap_number, lap_data in enumerate(data.get("laps", []), start=1):
            self.laps.append({
                "lap_number": lap_number,
                "time": lap_data.get("time"),
                "pit_stop": lap_data.get(
                    "pitStop",
                    lap_data.get("pitstop", False),
                ),
                "fastest": lap_data.get(
                    "isFastest",
                    lap_data.get("fastest", False),
                ),
            })

        self.pits = [
            lap["lap_number"]
            for lap in self.laps
            if lap["pit_stop"]
        ]

        fastest_flags = [lap["fastest"] for lap in self.laps]
        if any(flag is True for flag in fastest_flags):
            self.fastest = True
        elif fastest_flags:
            self.fastest = False
        else:
            self.fastest = None

        self.fastest_lap_ms = data.get("fastest_lap_ms")

        raw_time_ms = data.get("total_time_ms")
        raw_time = data.get("total_time")

        if raw_time_ms is not None:
            self.total_time_ms = raw_time_ms
        elif isinstance(raw_time, (int, float)):
            self.total_time_ms = raw_time
        else:
            self.total_time_ms = None

        self.total_time = (
            raw_time if raw_time is not None else data.get("finish_time")
        )

        self.laps_completed = (
            len(self.laps) if self.laps else data.get("laps_completed")
        )

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "start_position": self.start_position,
            "position": self.position,
            "finished": self.finished,
            "dnf": self.dnf,
            "laps": self.laps,
            "pits": self.pits,
            "fastest": self.fastest,
            "fastest_lap_ms": self.fastest_lap_ms,
            "total_time_ms": self.total_time_ms,
            "total_time": self.total_time,
            "laps_completed": self.laps_completed,
        }

    @classmethod
    def from_dict(cls, data, heat):
        result = cls(data, heat)

        # Restore normalized values exactly as saved, rather than
        # re-deriving them from possibly incomplete lap data.
        result.pits = data.get("pits", result.pits)
        result.fastest = data.get("fastest", result.fastest)
        result.fastest_lap_ms = data.get(
            "fastest_lap_ms", result.fastest_lap_ms
        )
        result.total_time_ms = data.get(
            "total_time_ms", result.total_time_ms
        )
        result.total_time = data.get("total_time", result.total_time)
        result.laps_completed = data.get(
            "laps_completed", result.laps_completed
        )

        return result
