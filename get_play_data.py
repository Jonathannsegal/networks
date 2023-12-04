import argparse
import gzip
import os
import pathlib
import subprocess
from collections import defaultdict

import pandas as pd
import ujson as json
from tqdm import tqdm

original_data_folder = "./data/2016.NBA.Raw.SportVU.Game.Logs/"
output_folder = "./data/passing"

espn_csv_path = './espn/outcomes/NBA_PBP_2015-16.csv.gz'


def reformat_date_team(file_name):
    parts = file_name.split('.')
    date = parts[2] + parts[0] + parts[1]
    team = parts[-1]
    return f"{date}0{team}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate play data from existing passing data.')
    parser.add_argument('--game_name', type=str, default="01.22.2016.LAC.at.NYK",
                        help='File name without sffix of the game JSON data. Do not put in path, just the file name')
    parser.add_argument('--output_all_folder', type=str, default="./data/plays_all/",
                        help='Folder to output all play data')
    parser.add_argument('--output_filtered_folder', type=str, default="./data/plays_filtered/",
                        help='Folder to output filtered play data')
    args = parser.parse_args()

    file_name = args.game_name
    compressed_path = f"{original_data_folder}{file_name}.7z"
    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    pass_path = os.path.join(output_folder, file_name + '.json.gz')
    if not os.path.exists(pass_path):
        print("Parsing Passing Data from", pass_path)
        subprocess.run(["python", "get_passing_data.py", "--path", compressed_path, "--output_dir",
                        output_folder])

    with gzip.open(pass_path, 'rt', encoding='UTF-8') as file:
        print("Loading from parsed passing data:", pass_path)
        passing = json.load(file)
    print("Reading espn data from", espn_csv_path)
    espn_data = pd.read_csv(espn_csv_path, compression='gzip')
    this_game_espn_data = espn_data[espn_data['Game'] == reformat_date_team(file_name)]

    # (Quarter, SecLeft) to {Outcome, Weight}
    espn_quarter_secleft_to_event = this_game_espn_data[['Quarter', 'SecLeft', 'Outcome', 'Weight']].groupby(
        ['Quarter', 'SecLeft']).last().to_dict(orient='index')
    # Sort in that starts from (1, 720) to (1, ~0) to (2, 720)... eventually (4, ~0)
    espn_quarter_secleft_to_event = {k: espn_quarter_secleft_to_event[k] for k in
                                     sorted(espn_quarter_secleft_to_event, key=lambda x: (x[0], -x[1]))}
    # (Quarter, SecLeft) to {'pass_from', 'pass_to', 'snapshots', 'GameClock', 'Quarter', 'ShotClock', 'distance', 'average_speed', 'pass_duration'}
    # Sorted in that starts from (1, 720) to (1, ~0) to (2, 720)... eventually (4, ~0)
    # Where `snapshots` is a list of {'Ball', 'HomePlayers', 'GuestPlayers', 'GameClock', 'Quarter', 'ShotClock'}
    passing_quarter_secleft_to_event = {(one_pass['Quarter'], one_pass['GameClock']): one_pass for event in passing for
                                        one_pass in event if one_pass['pass_duration'] > 0}

    final_result = defaultdict(dict)

    for quarter_id in tqdm(range(1, 4), desc="Processing Quarters"):
        play_id = 0
        espn_secleft_to_event = {k[1]: v for k, v in espn_quarter_secleft_to_event.items() if k[0] == quarter_id}
        espn_seclefts = list(espn_secleft_to_event.keys())
        while play_id < len(espn_secleft_to_event) - 1:
            sec_left = espn_seclefts[play_id]
            next_sec_left = espn_seclefts[play_id + 1]
            current_pass_key = list(passing_quarter_secleft_to_event.keys())[0]

            while current_pass_key[0] == quarter_id and current_pass_key[1] >= espn_seclefts[play_id + 1]:
                if "Weight" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]["Weight"] = espn_secleft_to_event[next_sec_left]['Weight']
                if "Outcome" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]['Outcome'] = espn_secleft_to_event[next_sec_left]['Outcome']
                if "SecLeft_From" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]["SecLeft_From"] = espn_seclefts[play_id]
                if "SecLeft_Until" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]["SecLeft_Until"] = espn_seclefts[play_id + 1]
                if "Quarter" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]['Quarter'] = quarter_id
                if "Passes" not in final_result[(quarter_id, play_id)]:
                    final_result[(quarter_id, play_id)]['Passes'] = []

                final_result[(quarter_id, play_id)]['Passes'].append(
                    passing_quarter_secleft_to_event.pop(current_pass_key))
                current_pass_key = list(passing_quarter_secleft_to_event.keys())[0]
            play_id += 1

    plays = [*final_result.values()]
    filtered_plays = [play for idx, play in final_result.items() if
                      play['Outcome'].split(" ")[1] in (
                              str(play["Passes"][-1]['pass_from']) + str(play["Passes"][-1]['pass_to']))]
    pathlib.Path(args.output_all_folder).mkdir(exist_ok=True)
    pathlib.Path(args.output_filtered_folder).mkdir(exist_ok=True)
    print("Saving results")
    json.dump(plays, open(os.path.join(args.output_all_folder, file_name + ".json"), "w+"))
    json.dump(filtered_plays, open(os.path.join(args.output_filtered_folder, file_name + ".json"), "w+"))
    print("Saved to ", os.path.join(args.output_all_folder, file_name + ".json"))
    print("Saved to ", os.path.join(args.output_filtered_folder, file_name + ".json"))
