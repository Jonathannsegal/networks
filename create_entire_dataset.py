import subprocess
import multiprocessing as mp
from glob import glob
import os

filenames = glob("data/2016.NBA.Raw.SportVU.Game.Logs/*.7z")

def run_command(game_name):
    subprocess.run(["python", "get_play_data.py", "--game_name", game_name])

if __name__ == '__main__':

    game_names_to_run = []

    for filename in filenames:
        file = filename.split('/')[-1]
        if file.startswith('2016'):
            continue
        
        game_name = file = file.replace('.7z', '')

        if os.path.exists(f'data/plays_all/{game_name}.json'):
            continue
        
        game_names_to_run.append(game_name)

    pool = mp.Pool(4)
    pool.map(run_command, game_names_to_run)
    pool.close()