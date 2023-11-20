import argparse

from Game import Game

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process arguments about an NBA game.')
    parser.add_argument('--path', type=str,
                        help='a path to json file to read the events from',
                        required=True)
    parser.add_argument('--event', type=int, default=0,
                        help="""an index of the event to create the animation to
                                (the indexing start with zero, if you index goes beyond out
                                the total number of events (plays), it will show you the last
                                one of the game)""")

    args = parser.parse_args()

    game = Game(path_to_json=args.path, event_index=args.event)
    game.read_json()
    #
    #
    # def filter_ball_attributes(ball):
    #     """Returns filtered attributes of the ball, excluding the 'color' attribute."""
    #     return {k: v for k, v in vars(ball).items() if k != "color"}
    #
    #
    # def filter_player_attributes(player):
    #     """Returns filtered attributes of a player, excluding the 'team' and 'color' attributes."""
    #     return {k: v for k, v in vars(player).items() if k not in ("team", "color")}
    #
    #
    # def format_players_by_team(moments, team_name):
    #     """Formats the player data for a given team."""
    #     return {
    #         game.event.player_ids_dict[player.id][0]: filter_player_attributes(player)
    #         for player in moments.players
    #         if player.team.name == team_name
    #     }
    #
    #
    # reformatted_dict = []
    #
    # for moment in game.event.moments:
    #     moment_data = {
    #         "Ball": filter_ball_attributes(moment.ball),
    #         "HomePlayers": format_players_by_team(moment, game.home_team.name),
    #         "GuestPlayers": format_players_by_team(moment, game.guest_team.name),
    #         "GameClock": moment.game_clock,
    #         "Quarter": moment.quarter,
    #         "ShotClock": moment.shot_clock
    #     }
    #     reformatted_dict.append(moment_data)

    # import matplotlib.pyplot as plt
    #
    # # Extract ball positions and sizes
    # ball_data = [entry["Ball"] for entry in reformatted_dict if
    #              all(key in entry["Ball"] for key in ["x", "y", "radius"])]
    #
    # # Split the data for plotting
    # x_positions = [data["x"] for data in ball_data]
    # y_positions = [data["y"] for data in ball_data]
    # sizes = [data["radius"] for data in ball_data]
    #
    # # It's possible that the radius values are too small or too big for visualization.
    # # If necessary, we can scale them using a scaling factor.
    # scaling_factor = 5  # Adjust this value based on your actual data and desired visualization.
    # scaled_sizes = [size * scaling_factor for size in sizes]
    #
    # # Plot
    # plt.figure(figsize=(10, 7))
    # plt.scatter(x_positions, y_positions, s=scaled_sizes, c='blue', marker='o', alpha=0.6)
    # plt.title("Ball Positions with Radius Indicating Height")
    # plt.xlabel("X Position")
    # plt.ylabel("Y Position")
    # plt.grid(True)
    # plt.show()

    game.start()
