import frosthex
import track

tracklist = frosthex.get_tracks

for t in tracklist["track_command_names"]:
    trackData = frosthex.get_track(t)
    