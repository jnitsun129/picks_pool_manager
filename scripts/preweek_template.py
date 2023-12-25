from jinja2 import Environment, FileSystemLoader
import pandas as pd
from createform import get_responses
from createform import upload_file_to_folder
from sendemail import send_postweek_pre_email


def calculate_margins(week):
    game_data = {}
    file_name = f'../week{week}/week{week}scores.txt'
    with open(file_name, "r", encoding='utf-8') as file:
        for line in file:
            if len(line.split(' ')) >= 5:
                parts = line.strip().split()
                game_name = ' '.join(parts[:3])
                score = parts[3]
                total = int(score.split('-')[0]) + int(score.split('-')[1])
                winner = parts[4]
                team_scores = score.split('-')
                margin = abs(int(team_scores[0]) - int(team_scores[1]))
                game_entry = {'margin': margin,
                              'winner': winner, 'total': total}
                game_data[game_name] = game_entry
        return game_data


def populate_covers(game_outcomes, game_lines):
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


def add_winners(covers, game_outcomes, week):
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


def get_lines(week):
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


def get_total_picks(week):
    players = {}
    with open('../utils/blank-points-template.txt', 'r') as file:
        for line in file:
            players[line.split(
                '-')[0][:-1]] = {'Overs': '0-0-0', 'Unders': '0-0-0', 'Favorites': '0-0-0', 'Underdogs': '0-0-0'}
    for w in range(1, int(week)):
        game_outcomes = calculate_margins(w)
        game_lines = get_lines(w)
        covers = populate_covers(game_outcomes, game_lines)
        weeks_picks = add_winners(covers, game_outcomes, w)
        for player, data in weeks_picks.items():
            if data['Favorite']['hit'] == 'Yes':
                record_arr = players[player]['Favorites'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Favorites'] = '-'.join(record_arr)
            if data['Underdog']['hit'] == 'Yes':
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Underdogs'] = '-'.join(record_arr)
            if data['Over']['hit'] == 'Yes':
                record_arr = players[player]['Overs'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Overs'] = '-'.join(record_arr)
            if data['Under']['hit'] == 'Yes':
                record_arr = players[player]['Unders'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Unders'] = '-'.join(record_arr)
            if data['Favorite']['hit'] == 'No':
                record_arr = players[player]['Favorites'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Favorites'] = '-'.join(record_arr)
            if data['Underdog']['hit'] == 'No':
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Underdogs'] = '-'.join(record_arr)
            if data['Over']['hit'] == 'No':
                record_arr = players[player]['Overs'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Overs'] = '-'.join(record_arr)
            if data['Under']['hit'] == 'No':
                record_arr = players[player]['Unders'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Unders'] = '-'.join(record_arr)
            if data['Favorite']['hit'] == 'Push':
                record_arr = players[player]['Favorites'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Favorites'] = '-'.join(record_arr)
            if data['Underdog']['hit'] == 'Push':
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Underdogs'] = '-'.join(record_arr)
            if data['Over']['hit'] == 'Push':
                record_arr = players[player]['Overs'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Overs'] = '-'.join(record_arr)
            if data['Under']['hit'] == 'Push':
                record_arr = players[player]['Unders'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Unders'] = '-'.join(record_arr)
    for player, data in players.items():
        win_count = 0
        loss_count = 0
        push_count = 0
        for _, record in data.items():
            try:
                win_count += int(record.split('-')[0])
                loss_count += int(record.split('-')[1])
                push_count += int(record.split('-')[2])
            except AttributeError:
                breakpoint()
        data['winnings'] = round(((90.91 * win_count) - (100 * loss_count)), 2)
        win_count = str(win_count)
        loss_count = str(loss_count)
        push_count = str(push_count)
        data['Overall'] = '-'.join([win_count, loss_count, push_count])
    return players


def populate_template(week, players_records):
    columns = ['Name', 'Favorite', 'Underdog', 'Over', 'Under']
    df = pd.read_csv(
        f'../week{week}/Greenwood-Picks-Pool-Week-{week}.csv', usecols=columns)
    data_dict = df.set_index('Name').to_dict(orient='index')
    points_dict = {}
    with open('../utils/points-cache.txt', 'r') as file:
        for line in file:
            name = line.rstrip().split('-')[0]
            points = float(line.rstrip().split('-')[1])
            points_dict[name] = points
    data = []
    for key, _ in data_dict.items():
        temp_dict = {}
        temp_dict['name'] = key
        temp_dict['points'] = points_dict[key + ' ']
        temp_dict['record'] = players_records[key]['Overall']
        temp_dict['Favorite'] = data_dict[key]['Favorite'].split('(')[1][:-1]
        temp_dict['Underdog'] = data_dict[key]['Underdog'].split('(')[1][:-1]
        temp_dict['Over'] = data_dict[key]['Over']
        temp_dict['Under'] = data_dict[key]['Under']
        data.append(temp_dict)

    data = sorted(data, key=lambda x: x['points'], reverse=True)
    env = Environment(loader=FileSystemLoader('..'))
    template = env.get_template('/templates/scoreboard_template.html')
    rendered_template = template.render(data=data, week=week)
    with open(f'../week{week}/scoreboard_week_{week}.html', 'w') as file:
        file.write(rendered_template)


def preweek_template_run(week):
    get_responses(week)
    populate_template(week, get_total_picks(week))
    upload_file_to_folder(file_name=f'Week{week}Results.html',
                          file_path=f'../week{week}/scoreboard_week_{week}.html', week=week, type='pre')
    print('File Uploaded')
    send_postweek_pre_email(week=week, type='pre')
    print('File Sent')
