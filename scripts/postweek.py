from jinja2 import Environment, FileSystemLoader
import requests
from createform import upload_file_to_folder
from sendemail import send_postweek_pre_email
from datetime import datetime, timezone
from utilities import populate_covers, add_winners, get_lines, calculate_margins


def get_score_results(week: int) -> None:
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    response = requests.get(url)
    if response.status_code == 200:
        now = datetime.now(timezone.utc)
        data = response.json()
        games = []
        for event in data["events"]:
            if event["season"]["year"] == 2023 and event["week"]["number"] == week:
                home_team = None
                away_team = None
                home_score = None
                away_score = None
                game_date = datetime.strptime(
                    event["date"], '%Y-%m-%dT%H:%M%SZ').replace(tzinfo=timezone.utc)
                if game_date < now:
                    for team in event["competitions"][0]["competitors"]:
                        if team["homeAway"] == "home":
                            home_team = team["team"]["displayName"]
                            home_team = home_team.split(
                                " ")[len(home_team.split(" ")) - 1]
                            home_score = team["score"]
                        else:
                            away_team = team["team"]["displayName"]
                            away_team = away_team.split(
                                " ")[len(away_team.split(" ")) - 1]
                            away_score = team["score"]
                    if int(home_score) > int(away_score):
                        games.append(
                            f"{away_team} @ {home_team} {home_score}-{away_score} {home_team}")
                    else:
                        games.append(
                            f"{away_team} @ {home_team} {away_score}-{home_score} {away_team}")
                else:
                    teams = event["name"].split(" at ")
                    home_team = teams[0].split(
                        " ")[len(teams[0].split(" ")) - 1]
                    away_team = teams[1].split(
                        " ")[len(teams[1].split(" ")) - 1]
                    games.append(f"{home_team} @ {away_team}")

    with open(f'../week{week}/week{week}scores.txt', 'w') as file:
        for game in games:
            file.write(f'{game}\n')


def update_week_points(weeks_picks: dict, week: int) -> None:
    points_dict = {}
    file_name = f'../week{week}/week{week}points.txt'
    with open(file_name, 'r') as file:
        for line in file:
            name = line.rstrip().split('-')[0].rstrip()
            points = float(line.rstrip().split('-')[1])
            points_dict[name] = 0
    for person, picks in weeks_picks.items():
        for _, pick in picks.items():
            if pick['hit'] == 'Yes':
                points_dict[person] += 1.0
            elif pick['hit'] == 'Push':
                points_dict[person] += 0.5
    with open(file_name, 'w') as file:
        for person, points in points_dict.items():
            file.write(person + f' -{points}\n')


def get_week_records(week: int) -> dict:
    players = {}
    w = week
    with open('../utils/blank-points-template.txt', 'r') as file:
        for line in file:
            players[line.split(
                '-')[0][:-1]] = {'Overs': '0-0-0', 'Unders': '0-0-0', 'Favorites': '0-0-0', 'Underdogs': '0-0-0'}
    game_outcomes = calculate_margins(w)
    game_lines = get_lines(w)
    covers = populate_covers(game_outcomes, game_lines)
    weeks_picks = add_winners(covers, game_outcomes, w)
    for player, data in weeks_picks.items():
        if data['Favorite']['hit'] == 'Yes':  # hit
            record_arr = players[player]['Favorites'].split('-')
            record_arr[0] = int(record_arr[0])
            record_arr[0] += 1
            record_arr[0] = str(record_arr[0])
            players[player]['Favorites'] = '-'.join(record_arr)
        if data['Underdog']['hit'] == 'Yes':  # hit
            record_arr = players[player]['Underdogs'].split('-')
            record_arr[0] = int(record_arr[0])
            record_arr[0] += 1
            record_arr[0] = str(record_arr[0])
            players[player]['Underdogs'] = '-'.join(record_arr)
        if data['Over']['hit'] == 'Yes':  # hit
            record_arr = players[player]['Overs'].split('-')
            record_arr[0] = int(record_arr[0])
            record_arr[0] += 1
            record_arr[0] = str(record_arr[0])
            players[player]['Overs'] = '-'.join(record_arr)
        if data['Under']['hit'] == 'Yes':  # hit
            record_arr = players[player]['Unders'].split('-')
            record_arr[0] = int(record_arr[0])
            record_arr[0] += 1
            record_arr[0] = str(record_arr[0])
            players[player]['Unders'] = '-'.join(record_arr)
        if data['Favorite']['hit'] == 'No':  # loss
            record_arr = players[player]['Favorites'].split('-')
            record_arr[1] = int(record_arr[1])
            record_arr[1] += 1
            record_arr[1] = str(record_arr[1])
            players[player]['Favorites'] = '-'.join(record_arr)
        if data['Underdog']['hit'] == 'No':  # loss
            record_arr = players[player]['Underdogs'].split('-')
            record_arr[1] = int(record_arr[1])
            record_arr[1] += 1
            record_arr[1] = str(record_arr[1])
            players[player]['Underdogs'] = '-'.join(record_arr)
        if data['Over']['hit'] == 'No':  # loss
            record_arr = players[player]['Overs'].split('-')
            record_arr[1] = int(record_arr[1])
            record_arr[1] += 1
            record_arr[1] = str(record_arr[1])
            players[player]['Overs'] = '-'.join(record_arr)
        if data['Under']['hit'] == 'No':  # loss
            record_arr = players[player]['Unders'].split('-')
            record_arr[1] = int(record_arr[1])
            record_arr[1] += 1
            record_arr[1] = str(record_arr[1])
            players[player]['Unders'] = '-'.join(record_arr)
        if data['Favorite']['hit'] == 'Push':  # push
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


def populate_template(week_results: dict, week_records: dict, week: int) -> None:
    points_dict = {}
    file_name = f'../week{week}/week{week}points.txt'
    with open(file_name, 'r') as file:
        for line in file:
            name = line.rstrip().split('-')[0]
            points = float(line.rstrip().split('-')[1])
            points_dict[name] = points
    data = []
    for key, value in week_results.items():
        temp_dict = {}
        temp_dict['name'] = key
        temp_dict['points'] = points_dict[key + ' ']
        temp_dict['record'] = week_records[key]['Overall']
        temp_dict['Favorite'] = {'hit': week_results[key]['Favorite']['hit'], 'pick': week_results[key]['Favorite']['pick'].split('(')[
            1][:-1]}
        temp_dict['Underdog'] = {'hit': week_results[key]['Underdog']['hit'], 'pick': week_results[key]['Underdog']['pick'].split('(')[
            1][:-1]}
        temp_dict['Over'] = week_results[key]['Over']
        temp_dict['Under'] = week_results[key]['Under']
        data.append(temp_dict)
    data = sorted(data, key=lambda x: x['points'], reverse=True)
    env = Environment(loader=FileSystemLoader('..'))
    template = env.get_template('/templates/post_scoreboard_template.html')

    rendered_template = template.render(data=data, week=week)

    with open(f'../week{week}/post_scoreboard_week_{week}.html', 'w') as file:
        file.write(rendered_template)


def curr_week_run(week: int) -> None:
    game_outcomes = calculate_margins(week)
    game_lines = get_lines(week)
    covers = populate_covers(game_outcomes, game_lines)
    weeks_picks = add_winners(covers, game_outcomes, week)
    update_week_points(weeks_picks, week)
    populate_template(weeks_picks, get_week_records(week), week)


def get_total_picks(week: int) -> dict:
    players = {}
    with open('../utils/blank-points-template.txt', 'r') as file:
        for line in file:
            players[line.split(
                '-')[0][:-1]] = {'Overs': '0-0-0', 'Unders': '0-0-0', 'Favorites': '0-0-0', 'Underdogs': '0-0-0', 'Points': 0.0}
    for w in range(1, int(week) + 1):
        game_outcomes = calculate_margins(w)
        game_lines = get_lines(w)
        covers = populate_covers(game_outcomes, game_lines)
        weeks_picks = add_winners(covers, game_outcomes, w)
        for player, data in weeks_picks.items():
            if data['Favorite']['hit'] == 'Yes':  # hit
                record_arr = players[player]['Favorites'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Favorites'] = '-'.join(record_arr)
                players[player]['Points'] += 1
            if data['Underdog']['hit'] == 'Yes':  # hit
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Underdogs'] = '-'.join(record_arr)
                players[player]['Points'] += 1
            if data['Over']['hit'] == 'Yes':  # hit
                record_arr = players[player]['Overs'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Overs'] = '-'.join(record_arr)
                players[player]['Points'] += 1
            if data['Under']['hit'] == 'Yes':  # hit
                record_arr = players[player]['Unders'].split('-')
                record_arr[0] = int(record_arr[0])
                record_arr[0] += 1
                record_arr[0] = str(record_arr[0])
                players[player]['Unders'] = '-'.join(record_arr)
                players[player]['Points'] += 1
            if data['Favorite']['hit'] == 'No':  # loss
                record_arr = players[player]['Favorites'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Favorites'] = '-'.join(record_arr)
            if data['Underdog']['hit'] == 'No':  # loss
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Underdogs'] = '-'.join(record_arr)
            if data['Over']['hit'] == 'No':  # loss
                record_arr = players[player]['Overs'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Overs'] = '-'.join(record_arr)
            if data['Under']['hit'] == 'No':  # loss
                record_arr = players[player]['Unders'].split('-')
                record_arr[1] = int(record_arr[1])
                record_arr[1] += 1
                record_arr[1] = str(record_arr[1])
                players[player]['Unders'] = '-'.join(record_arr)
            if data['Favorite']['hit'] == 'Push':  # push
                record_arr = players[player]['Favorites'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Favorites'] = '-'.join(record_arr)
                players[player]['Points'] += 0.5
            if data['Underdog']['hit'] == 'Push':
                record_arr = players[player]['Underdogs'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Underdogs'] = '-'.join(record_arr)
                players[player]['Points'] += 0.5
            if data['Over']['hit'] == 'Push':
                record_arr = players[player]['Overs'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Overs'] = '-'.join(record_arr)
                players[player]['Points'] += 0.5
            if data['Under']['hit'] == 'Push':
                record_arr = players[player]['Unders'].split('-')
                record_arr[2] = int(record_arr[2])
                record_arr[2] += 1
                record_arr[2] = str(record_arr[2])
                players[player]['Unders'] = '-'.join(record_arr)
                players[player]['Points'] += 0.5
    for player, data in players.items():
        win_count = 0
        loss_count = 0
        push_count = 0
        for _, record in data.items():
            if type(record) != float:
                win_count += int(record.split('-')[0])
                loss_count += int(record.split('-')[1])
                push_count += int(record.split('-')[2])
        data['winnings'] = round(((90.91 * win_count) - (100 * loss_count)), 2)
        win_count = str(win_count)
        loss_count = str(loss_count)
        push_count = str(push_count)
        data['Overall'] = '-'.join([win_count,
                                    loss_count, push_count]) + ' (' + str(data['Points']) + ')'
    return players


def get_value(record: str) -> float:
    return float(record.split('(')[-1].rstrip(')'))


def populate_stats_template(week_results: dict, week: int) -> None:
    data = {
        'Favorites': [],
        'Overs': [],
        'Underdogs': [],
        'Unders': [],
        'Overall': [],
    }
    winnings = {}
    for name, records in week_results.items():
        data['Favorites'].append({
            'name': name,
            'record': records['Favorites']
        })
        data['Overs'].append({
            'name': name,
            'record': records['Overs']
        })
        data['Underdogs'].append({
            'name': name,
            'record': records['Underdogs']
        })
        data['Unders'].append({
            'name': name,
            'record': records['Unders']
        })
        data['Overall'].append({
            'name': name,
            'record': records['Overall']
        })
        if records['winnings'] > 0:
            winnings[
                f"If {name} bet $100 on each pick, he would be up: ${records['winnings']}"] = records['winnings']
        elif records['winnings'] < 0:
            winnings[
                f"If {name} bet $100 on each pick, he would be down: ${abs(records['winnings'])}"] = records['winnings']
        else:
            winnings[
                f"If {name} bet $100 on each pick, he would be dead even"] = 0
    for type, category in data.items():
        if type != 'Overall':
            category.sort(key=lambda x: (
                int(x['record'].split('-')[1]), -int(x['record'].split('-')[0])), reverse=False)
        else:
            category.sort(key=lambda x: get_value(x['record']), reverse=True)
    env = Environment(loader=FileSystemLoader('..'))
    template = env.get_template('/templates/stats_template.html')
    rendered_template = template.render(
        data=data, week=week, winnings=winnings)
    output_file_path = f'../stats/post_week_{week}_stats.html'
    with open(output_file_path, 'w') as file:
        file.write(rendered_template)


def extract_content(html: str, tag: str) -> str:
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    start = html.find(start_tag) + len(start_tag)
    end = html.find(end_tag)
    return html[start:end].strip()


def combine_files(week: int) -> None:
    with open(f'../week{week}/post_scoreboard_week_{week}.html', 'r') as file:
        first_html = file.read()
        first_html_body = extract_content(first_html, 'body')
        first_html_style = extract_content(first_html, 'style')

    with open(f'../stats/post_week_{week}_stats.html', 'r') as file:
        second_html = file.read()
        second_html_body = extract_content(second_html, 'body')
        second_html_style = extract_content(second_html, 'style')

    combined_css = first_html_style + "\n\t\t\t" + second_html_style

    with open('../templates/combined_docs_template.html', 'r') as file:
        template = file.read()

    filled_template = template.replace('{{first_html_body}}', first_html_body)
    filled_template = filled_template.replace(
        '{{second_html_body}}', second_html_body)
    filled_template = filled_template.replace(
        '/* {{combined_css}} */', combined_css)
    filled_template = filled_template.replace('{{week}}', str(week))

    with open(f'../week{week}/results_and_stats_week{week}.html', 'w') as file:
        file.write(filled_template)


def update_all_points(week: int) -> None:
    names_arr = []
    with open("../utils/blank-points-template.txt", "r") as file:
        for line in file:
            names_arr.append(line.split("-")[0].rstrip())

    points_dict = {}

    for i in range(1, int(week) + 1):
        with open(f"../week{i}/week{i}points.txt", "r") as file:
            for line in file:
                name = line.split("-")[0].rstrip()
                if name not in points_dict:
                    points_dict[name] = float(line.split("-")[1].rstrip())
                else:
                    points_dict[name] += float(line.split("-")[1].rstrip())

    points_dict = dict(
        sorted(points_dict.items(), key=lambda item: item[1], reverse=True))

    with open("../utils/points-cache.txt", "w") as file:
        for name, points in points_dict.items():
            file.write(f'{name} -{points}\n')


def postweek_run(week: int) -> None:
    get_score_results(week)
    curr_week_run(week)
    populate_stats_template(get_total_picks(week), week)
    combine_files(week)
    upload_file_to_folder(file_name=f'Week{week}Results.html',
                          file_path=f'../week{week}/results_and_stats_week{week}.html', week=week)
    print('File Uploaded')
    send_postweek_pre_email(week)
    update_all_points(week)
