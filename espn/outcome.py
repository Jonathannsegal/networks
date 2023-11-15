import pandas as pd
import os
import glob
import re

def parse_play(play, away_team, home_team):
    if pd.isna(play) or play.strip() == '':
        return None

    play = play.replace(',', ';').replace('"', "'")

    # Exclude non-action plays like end of quarters or player substitutions
    if 'enters the game for' in play or 'End of' in play or 'ejected from game' in play or 'Instant Replay' in play:
        return 'Exclude Line'

    # Determine the team involved in the play
    # print(away_team, home_team, play)
    team = ""
    # team = away_team if play.startswith(f"{away_team} ") else home_team if play.startswith(f"{home_team} ") else None

    # Jump Ball
    if 'Jump ball' in play:
        return f"{team}jump ball"

    # Technical fouls
    tech_foul_match = re.match(r'(Def 3 sec|Off 3 sec|Tech) tech foul by (.*)', play)
    if tech_foul_match:
        foul_type, player = tech_foul_match.groups()
        return f"{team}{player} {foul_type} technical foul"

    # Timeouts
    timeout_match = re.match(r'(.*?)(?: (full|short|Official))? timeout', play)
    if timeout_match:
        team_name, timeout_type = timeout_match.groups()
        if not team_name.strip():
            return f"{timeout_type} timeout"
        else:
            return f"{team_name} {timeout_type} timeout"

    # Field Goal Made
    fg_made_match = re.match(r'(.*) makes (\d)-pt (.*) from (\d+) ft', play)
    if fg_made_match:
        player, points, shot_type, distance = fg_made_match.groups()
        return f"{team}{player} makes {points}-pt {shot_type} from {distance} ft"
    
    # Field Goals with assists
    fg_assist_match = re.match(r'(.*) (makes) (\d)-pt (.*) from (\d+) ft \(assist by (.*)\)', play)
    if fg_assist_match:
        player, action, points, shot_type, distance, assist_by = fg_assist_match.groups()
        return f"{team}{player} {action} {points}-pt {shot_type} from {distance} ft, assisted by {assist_by}"

    # Field Goals with "at rim"
    fg_rim_match = re.match(r'(.*) (makes|misses) (\d)-pt (.*) at rim', play)
    if fg_rim_match:
        player, action, points, shot_type = fg_rim_match.groups()
        return f"{team}{player} {action} {points}-pt {shot_type} at rim"

    # Field Goal Missed
    fg_missed_match = re.match(r'(.*) misses (\d)-pt (.*) from (\d+) ft', play)
    if fg_missed_match:
        player, shot_type, distance = fg_missed_match.groups()[:3]
        return f"{team}{player} misses {shot_type} from {distance} ft"
    
    # Field Goals
    fg_match = re.match(r'(.*) (misses|makes) (\d)-pt (.*?)(?: \(assist by (.*?)\))?', play)
    if fg_match:
        player, action, shot_type, shot_desc, assist_by = fg_match.groups()
        assist_str = f" (assist by {assist_by})" if assist_by else ""
        return f"{team}{player} {action} {shot_type}-pt {shot_desc}{assist_str}"

    # Rebounds
    rebound_match = re.match(r'(Offensive|Defensive) rebound by (.*)', play)
    if rebound_match:
        rebound_type, player = rebound_match.groups()
        return f"{team}{player} {rebound_type.lower()} rebound"

    # Turnovers
    turnover_match = re.match(r'Turnover by (.*) \((.*)\)', play)
    if turnover_match:
        player, turnover_type = turnover_match.groups()
        return f"{team}{player} turnover ({turnover_type})"

    # Fouls
    foul_match = re.match(r'(.+?) foul( type \d+)? by (.*) (?:\(drawn by (.*)\))?', play)
    if foul_match:
        foul_type, player, _, drawn_by = foul_match.groups()
        drawn_by_str = f" (drawn by {drawn_by})" if drawn_by else ""
        return f"{team}{player} {foul_type} foul {drawn_by_str}"
    
    specific_foul_match = re.match(r'Offensive foul by', play)
    if specific_foul_match:
        return f"{team}Offensive foul"
    
    # Violations and Fouls
    violation_match = re.match(r'Violation by (.*) \((.*)\)', play)
    foul_match = re.match(r'(Technical|Personal) foul by (.*)', play)
    if violation_match or foul_match:
        return f"{team}{play}"

    # General Free Throws (including technical and flagrant)
    ft_general_match = re.match(r'(.*) (makes|misses)( technical| flagrant| clear path)? free throw(?: (\d+)(?: of (\d+))?)?', play)
    if ft_general_match:
        player, action, _, current, total = ft_general_match.groups()
        points = '1' if action == 'makes' else '0'
        # Handling the case where 'current' or 'total' might be None
        current = current or '1'  # Assuming '1' if not specified
        total = total or current   # Total is same as current if not specified
        return f"{team}{player} {action} free throw {current} of {total}, {points} points"

    # Other specific plays not covered
    return f"Unidentified Play: {play}"

def assign_weight(outcome):
    if outcome is None:
        return 0

    # Assigning different weights to different play types
    if '3' in outcome:
        return 3
    elif '2' in outcome or 'free throw' in outcome:
        return 2
    elif 'offensive rebound' in outcome or 'assist' in outcome or 'steal' in outcome:
        return 1  # Positive weight for offensive rebounds
    elif 'defensive rebound' in outcome or 'block' in outcome:
        return -1  # Negative weight for defensive rebounds
    elif 'turnover' in outcome or 'foul' in outcome:
        return -2
    else:
        return 0

def process_file(file_path, output_folder):
    nba_data = pd.read_csv(file_path)
    relevant_columns = ['URL', 'Location', 'Date', 'Time', 'Quarter', 'SecLeft', 'AwayTeam', 'HomeTeam', 'AwayPlay', 'HomePlay']
    nba_relevant_data = nba_data[relevant_columns].copy()
    nba_relevant_data['Game'] = nba_relevant_data['URL'].apply(lambda x: x.split('/')[-1].split('.')[0])
    nba_relevant_data = nba_relevant_data.drop('URL', axis=1)
    nba_relevant_data['Outcome'] = nba_relevant_data.apply(
        lambda row: parse_play(row['AwayPlay'], row['AwayTeam'], row['HomeTeam']) or
                    parse_play(row['HomePlay'], row['AwayTeam'], row['HomeTeam']),
        axis=1
    )
    nba_relevant_data = nba_relevant_data.drop(['AwayPlay', 'HomePlay'], axis=1)

    # Exclude lines marked as 'Exclude Line'
    nba_relevant_data = nba_relevant_data[nba_relevant_data['Outcome'] != 'Exclude Line']

    # Add weights column
    nba_relevant_data['Weight'] = nba_relevant_data['Outcome'].apply(assign_weight)

    file_name = os.path.basename(file_path)
    output_file_path = os.path.join(output_folder, file_name)
    nba_relevant_data.to_csv(output_file_path, index=False)

data_folder = 'data'
outcomes_folder = 'outcomes'
if not os.path.exists(outcomes_folder):
    os.makedirs(outcomes_folder)

for file_path in glob.glob(os.path.join(data_folder, '*.csv')):
    process_file(file_path, outcomes_folder)
