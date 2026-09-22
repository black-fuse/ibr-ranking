
SOURCE_OFFSETS = {
    "frosthex": 1000000,
    "boatlabs": 2000000,
    "brwc": 3000000,
    "bbrl": 4000000
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