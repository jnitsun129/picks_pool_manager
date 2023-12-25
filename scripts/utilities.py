import pandas as pd


def populate_covers(game_outcomes: dict, game_lines: dict) -> dict:
    result_dict = {}
    result_dict['Favorite'] = []
    result_dict['SpreadPush'] = []
    result_dict['Underdog'] = []
    result_dict['Over'] = []
    result_dict['TotalPush'] = []
    result_dict['Under'] = []
    for game, result in game_outcomes.items():
        spread = float(game_lines['Favorite']
                       [game].split(' ')[1].split('-')[1])
        favorite = game_lines['Favorite'][game].split(' ')[0]
        over_under = float(game_lines['Over'][game].split(' ')[1])
        margin = result['margin']
        winner = result['winner']
        total = float(result['total'])
        if total < over_under:
            result_dict['Under'].append(game)
        elif total > over_under:
            result_dict['Over'].append(game)
        else:
            result_dict['TotalPush'].append(game)
        if winner == favorite:
            if margin > spread:
                result_dict['Favorite'].append(game)
            if margin < spread:
                result_dict['Underdog'].append(game)
            if margin == spread:
                result_dict['SpreadPush'].append(game)
        else:
            result_dict['Underdog'].append(game)
    return result_dict


def add_winners(covers: dict, game_outcomes: dict, week: int) -> dict:
    columns = ['Name', 'Favorite', 'Underdog', 'Over', 'Under']
    df = pd.read_csv(
        f'../week{week}/Greenwood-Picks-Pool-Week-{week}.csv', usecols=columns)

    weeks_picks = df.set_index('Name').to_dict(orient='index')
    for key, picks in weeks_picks.items():
        for pick in picks:
            temp_pick = picks[pick]
            picks[pick] = {}
            picks[pick]['pick'] = temp_pick
            picks[pick]['hit'] = 'Pending'

    for person, picks in weeks_picks.items():
        person = person + ' '
        for key, pick in picks.items():
            game_pick = pick['pick']
            if key == "Favorite" or key == "Underdog":
                game_pick = game_pick.split('(')[0].strip()
                if game_pick in covers[key]:
                    pick['hit'] = 'Yes'
                elif game_pick in covers['SpreadPush']:
                    pick['hit'] = 'Push'
                else:
                    if game_pick in game_outcomes:
                        pick['hit'] = 'No'
            else:
                game_pick = game_pick.split('(')[0].strip()
                if game_pick in covers[key]:
                    pick['hit'] = 'Yes'
                elif game_pick in covers['TotalPush']:
                    pick['hit'] = 'No'
                else:
                    if game_pick in game_outcomes:
                        pick['hit'] = 'No'
    return weeks_picks


def get_lines(week: int) -> dict:
    game_dict = {}
    with open(f'../week{week}/week{week}entry.txt', 'r') as file:
        curr_key = ""
        for line in file:
            if line.rstrip() == 'Favorite':
                curr_key = 'Favorite'
                game_dict[curr_key] = {}
            elif line.rstrip() == 'Underdog':
                curr_key = 'Underdog'
                game_dict[curr_key] = {}
            elif line.rstrip() == 'Over':
                curr_key = 'Over'
                game_dict[curr_key] = {}
            elif line.rstrip() == 'Under':
                curr_key = 'Under'
                game_dict[curr_key] = {}
            else:
                matchup = line.split('(')[0].rstrip()
                spread = line.split('(')[1].rstrip()[:-1]
                game_dict[curr_key][matchup] = spread
    return game_dict


def calculate_margins(week: int) -> dict:
    game_data = {}
    file_name = f'../week{week}/week{week}scores.txt'
    with open(file_name, "r") as file:
        for line in file:
            if len(line.split(' ')) >= 5:
                parts = line.strip().split()
            # First 3 values represent the game
                game_name = ' '.join(parts[:3])
                score = parts[3]  # Score is the 4th value
                total = int(score.split('-')[0]) + int(score.split('-')[1])
                winner = parts[4]  # Winner is the last value
                team_scores = score.split('-')
                margin = abs(int(team_scores[0]) - int(team_scores[1]))
                game_entry = {'margin': margin,
                              'winner': winner, 'total': total}
                game_data[game_name] = game_entry
        return game_data
