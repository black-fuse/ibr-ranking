
SOURCE_OFFSETS = {
    "frosthex": 1000000,
    "boatlabs": 2000000,
    "brwc": 3000000,
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

    def to_dict(self):
        return self.__dict__


class Performance:
    def __init__(self, data, track_id):
        self.player_uuid = data["player_uuid"]
        self.track_id = track_id
        self.time = data["time"]
        self.date = data["date"]
        self.position = None

    def to_dict(self):
        return self.__dict__

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
        return self.__dict__