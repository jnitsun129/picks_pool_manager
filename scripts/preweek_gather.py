import requests
import pandas as pd
from bs4 import BeautifulSoup
import shutil
from createform import create_form
import os
from sendemail import send_preweek_form


def create_week_folder(week_num):
    folder_name = f'../week{week_num}'
    os.makedirs(folder_name, exist_ok=True)
    entry_filename = os.path.join(folder_name, f'week{week_num}entry.txt')
    with open(entry_filename, 'w') as entry_file:
        entry_file.write('This is the entry file for week {week_num}.')
    scores_filename = os.path.join(folder_name, f'week{week_num}scores.txt')
    with open(scores_filename, 'w') as scores_file:
        scores_file.write('This is the scores file for week {week_num}.')
    picks_filename = os.path.join(
        folder_name, f'Greenwood-Picks-Pool-Week-{week_num}.csv')
    with open(picks_filename, 'w') as picks_file:
        picks_file.write('This is the picks file for week {week_num}')
    doc_id_filename = os.path.join(folder_name, f'week{week_num}doc_id.txt')
    with open(doc_id_filename, 'w') as doc_id:
        doc_id.write('doc_id_holder')
    template_filename = '../utils/blank-points-template.txt'
    points_filename = os.path.join(folder_name, f'week{week_num}points.txt')
    shutil.copy(template_filename, points_filename)


def get_weeks_matchups(week):
    url = f"https://www.vegasinsider.com/nfl/nfl-odds-week-{week}-2023/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    for table in tables:
        df = pd.read_html(str(table))[0]
        break
    data_dict = df.set_index('Matchup').to_dict(orient='index')
    transformed_data = {'Favorite': {},
                        'Underdog': {}, 'Over': {}, 'Under': {}}
    for matchup, values in data_dict.items():
        home_team = matchup.split('vs')[0].strip()
        away_team = matchup.split('vs')[1].strip()
        spread = values['Spread'].split(' ')[0]
        total = float(values['Total'].split(' ')[0][1:])
        if spread[0] == '-':
            favorite = home_team
            underdog = away_team
        else:
            favorite = away_team
            underdog = home_team
        spread = float(spread[1:])
        transformed_data['Favorite'][f'{away_team} @ {home_team}'] = f'({favorite} -{spread})'
        transformed_data['Underdog'][f'{away_team} @ {home_team}'] = f'({underdog} +{spread})'
        transformed_data['Over'][f'{away_team} @ {home_team}'] = f'(O {total})'
        transformed_data['Under'][f'{away_team} @ {home_team}'] = f'(U {total})'
    return transformed_data


def write_entry_data(games_data, week):
    with open(f'../week{week}/week{week}entry.txt', 'w') as file:
        for category, data in games_data.items():
            file.write(category + '\n')
            for game, info in data.items():
                file.write(f'{game} {info}\n')


def gather_run(week):
    create_week_folder(week)
    write_entry_data(get_weeks_matchups(week), week)
    create_form(week)
    print("Form Created")
    send_preweek_form(week)
    print("Form Sent")
