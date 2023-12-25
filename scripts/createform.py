from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import csv
import json

SCOPES = ["https://www.googleapis.com/auth/forms.body",
          "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = '../google-api/account.json'


def get_question_id(response):
    question_id = response['replies'][0]['createItem']['questionId'][0]
    return question_id


def create_form(week, folder_id='1Nyqd7TeL8OgHtmKDc3kaQKjBgWDT9L2J'):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    form_service = build("forms", "v1", credentials=credentials)
    drive_service = build("drive", "v3", credentials=credentials)
    ids = {}
    NEW_FORM = {
        "info": {
            "title": f"Greenwood Picks Pool Week {week}",
        }
    }

    names_arr = []
    with open('../blank-points-template.txt', 'r') as f:
        for line in f:
            names_arr.append({"value": line.strip().split('-')[0].rstrip()})

    games = {}
    with open(f'../week{week}/week{week}entry.txt', 'r') as f:
        curr_type = ''
        for line in f:
            line = line.rstrip()
            if line == 'Favorite' or line == 'Underdog' or line == 'Over' or line == 'Under':
                curr_type = line
            else:
                if curr_type not in games:
                    games[curr_type] = [{"value": line}]
                else:
                    games[curr_type].append({"value": line})

    NAME = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": (
                            "Name"
                        ),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": names_arr,
                                },
                            }
                        },
                    },
                    "location": {"index": 0},
                }
            }
        ]
    }

    FAVORITE = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": (
                            "Favorite"
                        ),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": games['Favorite'],
                                },
                            }
                        },
                    },
                    "location": {"index": 1},
                }
            }
        ]
    }

    UNDERDOG = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": (
                            "Underdog"
                        ),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": games['Underdog'],
                                },
                            }
                        },
                    },
                    "location": {"index": 2},
                }
            }
        ]
    }

    OVER = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": (
                            "Over"
                        ),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": games['Over'],
                                },
                            }
                        },
                    },
                    "location": {"index": 3},
                }
            }
        ]
    }

    UNDER = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": (
                            "Under"
                        ),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": games['Under'],
                                },
                            }
                        },
                    },
                    "location": {"index": 4},
                }
            }
        ]
    }

    result = form_service.forms().create(body=NEW_FORM).execute()

    question_setting = (
        form_service.forms()
        .batchUpdate(formId=result["formId"], body=NAME)
        .execute()
    )
    ids[get_question_id(question_setting)] = 'Name'

    question_setting = (
        form_service.forms()
        .batchUpdate(formId=result["formId"], body=FAVORITE)
        .execute()
    )

    ids[get_question_id(question_setting)] = 'Favorite'

    question_setting = (
        form_service.forms()
        .batchUpdate(formId=result["formId"], body=UNDERDOG)
        .execute()
    )

    ids[get_question_id(question_setting)] = 'Underdog'

    question_setting = (
        form_service.forms()
        .batchUpdate(formId=result["formId"], body=OVER)
        .execute()
    )

    ids[get_question_id(question_setting)] = 'Over'

    question_setting = (
        form_service.forms()
        .batchUpdate(formId=result["formId"], body=UNDER)
        .execute()
    )

    ids[get_question_id(question_setting)] = 'Under'

    form_id = result['formId']

    ids['Form_Id'] = form_id

    form_file = drive_service.files().get(
        fileId=form_id, fields='id, parents').execute()
    previous_parents = ",".join(form_file.get('parents'))

    file = drive_service.files().update(
        fileId=form_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

    get_result = form_service.forms().get(formId=result["formId"]).execute()
    with open(f'../week{week}/form_id_{week}.json', 'w') as f:
        json.dump(ids, f, indent=4)
    if get_result is not None:
        print(result["formId"])
        print("Done!")


def get_responses(week):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    with open(f'../week{week}/form_id_{week}.json', 'r') as f:
        ids = json.load(f)
    form_id = ids['Form_Id']
    form_service = build("forms", "v1", credentials=credentials)
    responses_arr = []
    result = form_service.forms().responses().list(formId=form_id).execute()
    with open('../form_responses.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for response in result.get('responses', []):
            temp_dict = {}
            for key, val in response['answers'].items():
                temp_dict[ids[key]] = val['textAnswers']['answers'][0]['value']
            responses_arr.append(temp_dict)

    csv_file_name = f'../week{week}/Greenwood-Picks-Pool-Week-{week}.csv'

    with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['Name', 'Favorite', 'Underdog', 'Over', 'Under']

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for row in responses_arr:
            writer.writerow(row)

    return responses_arr


def upload_file_to_folder(file_path, file_name, week, type='post', file_mime_type='application/html', folder_id='1Nyqd7TeL8OgHtmKDc3kaQKjBgWDT9L2J',):
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    SERVICE_ACCOUNT_FILE = '../google-api/account.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=credentials)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype=file_mime_type)

    file = drive_service.files().create(
        body=file_metadata, media_body=media, fields='id').execute()
    with open(f'../week{week}/week{week}{type}doc_id.txt', 'w') as f:
        f.write(file.get('id'))
    print('Uploaded File ID: %s' % file.get('id'))
