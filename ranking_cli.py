from ranking import RankingSystem


def clear():
    print("\033[2J\033[H", end="")


def format_time(value):

    if value is None:
        return "N/A"

    try:
        value = float(value)

        minutes = int(value // 60)
        seconds = value % 60

        return f"{minutes}:{seconds:06.3f}"

    except (ValueError, TypeError):
        return str(value)


def print_player(ranking, stats):

    if not stats:
        print("Player not found.")
        return

    name = ranking.get_name(stats.uuid)
    rank = ranking.get_rank(stats.uuid)

    print()
    print("=" * 60)
    print(f"Player:       {name}")
    print(f"UUID:         {stats.uuid}")
    print(f"Rank:         #{rank}")
    print(f"Score:        {stats.score:.2f}")
    print("-" * 60)
    print(f"Performances: {stats.performances}")
    print(f"Tracks:       {len(stats.tracks)}")
    print(f"Coverage:     {stats.coverage:.1f}%")
    print(f"Average pos:  {stats.average_position:.2f}")
    print(f"Best pos:     #{stats.best_position}")
    print(f"track_records:{stats.track_records}")
    print(f"Podiums:      {stats.podiums}")
    print(f"Top 5:        {stats.top_5}")
    print(f"Top 10:       {stats.top_10}")
    print(f"Best time:    {format_time(stats.best_time)}")
    print("=" * 60)
    print()


def show_rankings(ranking, limit=25):

    ranked = ranking.rankings(limit)

    print()
    print(
        f"{'Rank':<6}"
        f"{'Player':<25}"
        f"{'Score':>10}"
        f"{'Tracks':>9}"
        f"{'Avg Pos':>9}"
        f"{'records':>7}"
    )

    print("-" * 70)

    for position, stats in enumerate(ranked, start=1):

        name = ranking.get_name(stats.uuid)

        # Prevent giant Discord names destroying the table.
        if len(name) > 23:
            name = name[:20] + "..."

        print(
            f"{position:<6}"
            f"{name:<25}"
            f"{stats.score:>10.2f}"
            f"{len(stats.tracks):>9}"
            f"{stats.average_position:>9.2f}"
            f"{stats.track_records:>7}"
        )

    print()


def search_players(ranking, query):

    results = ranking.search(query)

    if not results:
        print("No players found.")
        return

    print()

    for stats in results[:25]:

        print(
            f"{ranking.get_name(stats.uuid):<25} "
            f"#{ranking.get_rank(stats.uuid):<6} "
            f"{stats.score:.2f}"
        )

    print()


def compare_players(ranking, uuid1, uuid2):

    a = ranking.get_stats(uuid1)
    b = ranking.get_stats(uuid2)

    if not a:
        print(f"Player not found: {uuid1}")
        return

    if not b:
        print(f"Player not found: {uuid2}")
        return

    print()

    print(
        f"{'':<20}"
        f"{ranking.get_name(uuid1):>20}"
        f"{ranking.get_name(uuid2):>20}"
    )

    print("-" * 60)

    rows = [
        ("Rank", ranking.get_rank(uuid1), ranking.get_rank(uuid2)),
        ("Score", f"{a.score:.2f}", f"{b.score:.2f}"),
        ("Tracks", len(a.tracks), len(b.tracks)),
        ("Performances", a.performances, b.performances),
        ("Average position", f"{a.average_position:.2f}",
         f"{b.average_position:.2f}"),
        ("records", a.track_records, b.track_records),
        ("Podiums", a.podiums, b.podiums),
        ("Top 5", a.top_5, b.top_5),
        ("Top 10", a.top_10, b.top_10),
        ("Coverage", f"{a.coverage:.1f}%", f"{b.coverage:.1f}%"),
    ]

    for label, x, y in rows:

        print(
            f"{label:<20}"
            f"{str(x):>20}"
            f"{str(y):>20}"
        )

    print()


def show_track(ranking, track_id):

    track = ranking.get_track(track_id)

    if not track:
        print(f"Track {track_id} not found.")
        return

    print()
    print("=" * 70)
    print(f"Track: {track.get('display_name')}")
    print(f"ID: {track.get('id')}")
    print(f"Command: {track.get('command_name')}")
    print("=" * 70)

    leaderboard = track.get("leaderboard", [])

    for performance in leaderboard:

        uuid = performance.get("player_uuid")

        print(
            f"{performance.get('position', '?'):>4}. "
            f"{ranking.get_name(uuid):<25} "
            f"{format_time(performance.get('time'))}"
        )

    print()


def print_help():

    print("""
Commands
--------

rankings [number]
    Show rankings. Default: 25.

player <uuid>
    Show detailed player statistics.

search <name/uuid>
    Search for a player.

compare <uuid> <uuid>
    Compare two players.

track <id>
    Show a track leaderboard.

top records
    Show players with the most records.

top podiums
    Show players with the most podiums.

top coverage
    Show players with the most track coverage.

reload
    Reload JSON files and recalculate rankings.

help
    Show this help.

quit
    Exit.
""")


def show_special_ranking(ranking, category):

    stats = list(ranking.stats.values())

    if category == "records":
        stats.sort(key=lambda x: x.track_records, reverse=True)

    elif category == "podiums":
        stats.sort(key=lambda x: x.podiums, reverse=True)

    elif category == "coverage":
        stats.sort(key=lambda x: x.coverage, reverse=True)

    else:
        print(f"Unknown ranking: {category}")
        return

    print()

    for position, player in enumerate(stats[:25], start=1):

        name = ranking.get_name(player.uuid)

        if category == "records":
            value = player.track_records

        elif category == "podiums":
            value = player.podiums

        else:
            value = f"{player.coverage:.1f}%"

        print(
            f"{position:>3}. "
            f"{name:<25} "
            f"{value}"
        )

    print()


def main():

    print("Loading ranking data...")

    try:
        ranking = RankingSystem()

    except Exception as e:
        print(f"[ERROR] Failed to load ranking data: {e}")
        return

    print(
        f"Loaded {len(ranking.tracks)} tracks "
        f"and {len(ranking.stats)} players."
    )

    print("Type 'help' for commands.")
    print()

    while True:

        try:
            command = input("> ").strip()

        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not command:
            continue

        parts = command.split()

        cmd = parts[0].lower()

        # -------------------------------------------------
        # Quit
        # -------------------------------------------------

        if cmd in ("quit", "exit", "q"):
            break

        # -------------------------------------------------
        # Help
        # -------------------------------------------------

        elif cmd == "help":
            print_help()

        # -------------------------------------------------
        # Rankings
        # -------------------------------------------------

        elif cmd == "rankings":

            limit = 25

            if len(parts) > 1:

                try:
                    limit = int(parts[1])

                except ValueError:
                    print("Invalid number.")

            show_rankings(ranking, limit)

        # -------------------------------------------------
        # Player
        # -------------------------------------------------

        elif cmd == "player":

            if len(parts) < 2:
                print("Usage: player <uuid>")
                continue

            print_player(
                ranking,
                ranking.get_stats(parts[1])
            )

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        elif cmd == "search":

            if len(parts) < 2:
                print("Usage: search <name>")
                continue

            query = " ".join(parts[1:])

            search_players(ranking, query)

        # -------------------------------------------------
        # Compare
        # -------------------------------------------------

        elif cmd == "compare":

            if len(parts) < 3:
                print("Usage: compare <uuid1> <uuid2>")
                continue

            compare_players(
                ranking,
                parts[1],
                parts[2]
            )

        # -------------------------------------------------
        # Track
        # -------------------------------------------------

        elif cmd == "track":

            if len(parts) < 2:
                print("Usage: track <id>")
                continue

            show_track(
                ranking,
                parts[1]
            )

        # -------------------------------------------------
        # Special rankings
        # -------------------------------------------------

        elif cmd == "top":

            if len(parts) < 2:
                print("Usage: top <records|podiums|coverage>")
                continue

            show_special_ranking(
                ranking,
                parts[1].lower()
            )

        # -------------------------------------------------
        # Reload
        # -------------------------------------------------

        elif cmd == "reload":

            try:
                ranking.load()

                print(
                    f"Reloaded "
                    f"{len(ranking.tracks)} tracks and "
                    f"{len(ranking.stats)} players."
                )

            except Exception as e:
                print(f"[ERROR] Reload failed: {e}")

        else:
            print(
                f"Unknown command '{cmd}'. "
                "Type 'help'."
            )


if __name__ == "__main__":
    main()