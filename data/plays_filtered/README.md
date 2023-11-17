The JSON file is a list of Play dict
Play dict:
"Weight": e.g. 2
"Outcome": e.g. "A. Afflalo misses 2 from jump shot ft"
"SecLeft_From": e.g. 720
"SecLeft_Until": e.g. 700
"Quarter": 1
"Passes": List of dictionaries

For the "Passes" list of dictionaries:
Each dictionary represents a pass event.
Keys within each pass dictionary: "pass_from", "pass_to", "snapshots"

Values for "snapshots" (within each pass dictionary):
"Ball": Dictionary with keys: "x", "y", "radius"
"HomePlayers": Dictionary with player Name as keys and player information as sub-dictionaries
Sub-dictionary keys: "id", "x", "y"
"GuestPlayers": Dictionary with player Name as keys and player information as sub-dictionaries
Sub-dictionary keys: "id", "x", "y"
"GameClock": e.g. 720.0 (float)
"Quarter": e.g. 1 (int)
"ShotClock": e.g. 23.15 (float)