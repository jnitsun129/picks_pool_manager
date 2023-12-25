from jinja2 import Environment, FileSystemLoader
import pandas as pd
from createform import get_responses
from createform import upload_file_to_folder
from sendemail import send_postweek_pre_email
from utilities import populate_covers, add_winners, get_lines, calculate_margins


def get_total_picks(week: int) -> dict:
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


def populate_template(week: int, players_records: dict) -> None:
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


def preweek_template_run(week: int) -> None:
    get_responses(week)
    populate_template(week, get_total_picks(week))
    upload_file_to_folder(file_name=f'Week{week}Results.html',
                          file_path=f'../week{week}/scoreboard_week_{week}.html', week=week, type='pre')
    print('File Uploaded')
    send_postweek_pre_email(week=week, type='pre')
    print('File Sent')
