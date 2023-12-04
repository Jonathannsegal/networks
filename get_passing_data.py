import argparse
import gzip
import json
import os.path
import pathlib

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from py7zr import SevenZipFile
from tqdm.auto import tqdm

from Constant import *
from Event import Event
from Game import Game
from Team import Team


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False


# Argument parser setup
parser = argparse.ArgumentParser(description='Generate basketball game animation and passing data.')
parser.add_argument('--path', type=str, default="./data/0021500061.json", help='Path to game JSON data.')
parser.add_argument('--event', type=int, default=-1, help='Event index to visualize and analyze. -1 for all events')
parser.add_argument('--save_json', type=str2bool, default=True, help='Save passing data')
parser.add_argument('--gif', type=str2bool, default=False, help='Draw gifs for the input event')
parser.add_argument('--scaling_factor', type=int, default=5, help='Scaling factor for ball size in visualization.')
parser.add_argument('--output_dir', type=str, default='.', help='Outpuf folder')
args = parser.parse_args()

if args.path.endswith('.7z'):
    print("Uncompressing Basket Ball Event Data")
    with SevenZipFile(args.path, mode='r') as z:
        extract_path = os.path.splitext(args.path)[0]
        z.extractall(path=extract_path)
        data_frame = pd.read_json(os.path.join(extract_path, z.getnames()[0]))
else:
    data_frame = pd.read_json(args.path)

total_events = len(data_frame)

path = args.path
event = args.event
scaling_factor = args.scaling_factor


def filter_ball_attributes(ball):
    return {k: v for k, v in vars(ball).items() if k != "color"}


def filter_player_attributes(player):
    return {k: v for k, v in vars(player).items() if k not in ("team", "color")}


def format_players_by_team(game, moments, team_name):
    return {
        game.event.player_ids_dict[player.id][0]: filter_player_attributes(player)
        for player in moments.players
        if player.team.name == team_name
    }


def reformat_dict(game):
    time_snapshots = []
    for moment in game.event.moments:
        moment_data = {
            "Ball": filter_ball_attributes(moment.ball),
            "HomePlayers": format_players_by_team(game, moment, game.home_team.name),
            "GuestPlayers": format_players_by_team(game, moment, game.guest_team.name),
            "GameClock": moment.game_clock,
            "Quarter": moment.quarter,
            "ShotClock": moment.shot_clock
        }
        time_snapshots.append(moment_data)
    return time_snapshots


def get_speed(ball_1, ball_2):
    return np.sqrt((ball_1["x"] - ball_2["x"]) ** 2 + (ball_1["y"] - ball_2["y"]) ** 2)


def determine_possessor(data, speed_threshold, radius_threshold):
    last_possessors = [None] * len(data)
    last_possessor = None

    for idx in range(1, len(data)):
        ball_prev = data[idx - 1]["Ball"]
        ball_now = data[idx]["Ball"]

        speed = get_speed(ball_prev, ball_now)
        if speed < speed_threshold and ball_now["radius"] < radius_threshold and bool(data[idx]["HomePlayers"]) and bool(data[idx]["GuestPlayers"]):
            home_player, d1 = get_nearest_position(ball_now, data[idx]["HomePlayers"].values())
            guest_player, d2 = get_nearest_position(ball_now, data[idx]["GuestPlayers"].values())
            possessor = home_player if d1 < d2 else guest_player
            last_possessor = possessor['id']

        last_possessors[idx] = last_possessor

    return last_possessors


def plot_players(ax, players, color, marker, size=5):
    for player in players:
        ax.scatter(player["x"], player["y"], s=size, c=color, marker=marker)


def get_nearest_position(ball_position, players):
    distances = [np.sqrt((ball_position["x"] - player["x"]) ** 2 + (ball_position["y"] - player["y"]) ** 2) for player
                 in players]
    nearest_index = np.argmin(distances)
    return [*players][nearest_index], [*distances][nearest_index]


def initialize_plot():
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim([Constant.X_MIN, Constant.X_MAX])
    ax.set_ylim([Constant.Y_MIN, Constant.Y_MAX])
    ax.set_aspect('equal')
    return fig, ax


# Constants for ball possession
SPEED_THRESHOLD = 1
RADIUS_THRESHOLD = 5

from itertools import compress


def draw_gif(time_snapshots, event, game_name, game):
    ball_data = list(compress(time_snapshots,
                              ('x' in entry["Ball"] and 'y' in entry["Ball"] and 'radius' in entry["Ball"] for entry in
                               time_snapshots)))
    x_positions = [entry["Ball"]["x"] for entry in ball_data]
    y_positions = [entry["Ball"]["y"] for entry in ball_data]
    sizes = [entry["Ball"]["radius"] * scaling_factor for entry in ball_data]

    last_possessors = determine_possessor(time_snapshots, SPEED_THRESHOLD, RADIUS_THRESHOLD)
    progress_bar = tqdm(total=len(ball_data) + 1, desc="Rendering GIF", position=0, leave=True)
    fig, ax = initialize_plot()

    # Precompute plot limits and aspect ratio
    xlim = [Constant.X_MIN, Constant.X_MAX]
    ylim = [Constant.Y_MIN, Constant.Y_MAX]
    aspect = 'equal'

    def update(num, x_positions, y_positions, sizes, last_possessors):
        ax.clear()
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect(aspect)
        possessor_id = last_possessors[num]
        color = "red" if possessor_id is not None and game.event.player_ids_dict[possessor_id][
            1] == game.home_team else "blue"
        plot_players(ax, ball_data[num]["HomePlayers"].values(), 'orange', 'o')
        plot_players(ax, ball_data[num]["GuestPlayers"].values(), 'purple', 'o')
        home_player, _ = get_nearest_position(ball_data[num]["Ball"], ball_data[num]["HomePlayers"].values())
        guest_player, _ = get_nearest_position(ball_data[num]["Ball"], ball_data[num]["GuestPlayers"].values())

        # Draw last possessor with special handling
        for player, team_color, shape in [(home_player, 'orange', 'D'), (guest_player, 'purple', 's')]:
            size = 30 if player["id"] == last_possessors[num] else 20
            ax.scatter(player["x"], player["y"], s=size, c='red' if size == 30 else team_color, marker=shape)

        ax.scatter(x_positions[num], y_positions[num], s=sizes[num], c=color)
        progress_bar.update(1)

    ani = animation.FuncAnimation(fig, update, frames=len(ball_data),
                                  fargs=(x_positions, y_positions, sizes, last_possessors), repeat=False)

    plt.close(fig)
    ani.save(f'{game_name}_Event{event}.gif', writer='imagemagick', fps=25, dpi=80)
    progress_bar.close()


def read_json(game):
    index = game.event_index
    event = data_frame['events'][index]
    game.event = Event(event)
    game.home_team = Team(event['home']['teamid'])
    game.guest_team = Team(event['visitor']['teamid'])
    h = hash(json.dumps([*data_frame['events'][index]['moments']]))
    return h


def calculate_passing(time_snapshots, last_possessors, game):
    passing_list = []
    current_pass = None

    for idx in range(1, len(time_snapshots)):
        current_possessor = last_possessors[idx]
        previous_possessor = last_possessors[idx - 1]

        if current_possessor != previous_possessor:
            # End of the current pass and start of a new pass
            if current_pass is not None:
                # Calculate average speed
                total_speed = sum([get_speed(traj_i["Ball"], traj_j["Ball"])
                                   for traj_i, traj_j in zip(current_pass["snapshots"][:-1],
                                                             current_pass["snapshots"][1:])])
                current_pass["average_speed"] = total_speed / len(current_pass["snapshots"]) - 1
                # Calculate pass duration
                start_time = time_snapshots[idx - len(current_pass["snapshots"])]["GameClock"]
                end_time = time_snapshots[idx - 1]["GameClock"]
                current_pass["pass_duration"] = start_time - end_time

                passing_list.append(current_pass)

            # Start a new pass
            current_pass = {
                "pass_from": game.event.player_ids_dict[previous_possessor][
                    0] if previous_possessor else previous_possessor,
                "pass_to": game.event.player_ids_dict[current_possessor][0] if current_possessor else current_possessor,
                "snapshots": [],
                "GameClock": time_snapshots[idx]["GameClock"],
                "Quarter": time_snapshots[idx]["Quarter"],
                "ShotClock": time_snapshots[idx]["ShotClock"],
                "distance": 0  # This will be updated as trajectory is built
            }

        # Update the trajectory and distance of the current pass
        if current_pass is not None:
            ball_now = time_snapshots[idx]["Ball"]
            if len(current_pass["snapshots"]) > 0:
                ball_prev = current_pass["snapshots"][-1]["Ball"]
                current_pass["distance"] += get_speed(ball_prev, ball_now)
            current_pass["snapshots"].append(time_snapshots[idx])

    return passing_list


def main():
    game_name = ".".join(args.path.split('/')[-1].split('.')[:-1])
    input_event_id = args.event
    passing_list_list = []
    event_ids = [input_event_id]
    if input_event_id == -1:
        event_ids = [*range(total_events)]
    visited_events = set()
    time_snapshots = []
    for event_id in tqdm(event_ids, desc="Handling events"):
        game = Game(path_to_json=path, event_index=event_id)
        hash_value = read_json(game)
        if hash_value in visited_events:
            continue
        visited_events.add(hash_value)

        player_id_to_name_num = game.event.player_ids_dict
        time_snapshots.extend(reformat_dict(game))

    last_possessors = determine_possessor(time_snapshots, SPEED_THRESHOLD, RADIUS_THRESHOLD)
    if args.gif:
        draw_gif(time_snapshots, event_ids, game_name, game)

    passing_list = calculate_passing(time_snapshots, last_possessors, game)
    # time_to_dict = {(d['Quarter'], d['GameClock']): d for d in time_snapshots}

    passing_list_list.append(passing_list)  # Assuming this is for further usage

    # Save the passing list as JSON
    if args.save_json:
        if len(event_ids) == 1:
            event_id = f"_Event{event_ids[0]}"
        else:
            event_id = ""
        compressed_file_name = f"{game_name}{event_id}.json.gz"
        compressed_file_name = os.path.join(args.output_dir, compressed_file_name)
        pathlib.Path(args.output_dir).mkdir(exist_ok=True)
        print("Saving", compressed_file_name, "...\n To open later, use `gzip.open(FILE_NAME, 'wt', encoding='UTF-8')`")
        with gzip.open(compressed_file_name, 'wt', encoding='UTF-8') as json_file:
            json.dump(passing_list_list, json_file)
        print("Saved")


if __name__ == '__main__':
    main()
