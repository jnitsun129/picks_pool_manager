import base64
import io
import mimetypes
import os.path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = '../google-api/token.json'
SERVICE_ACCOUNT_FILE = '../google-api/account.json'


def create_message_with_attachment(sender, to, subject, message_text, file):
    message = MIMEMultipart()
    message['to'] = ', '.join(to)
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)
    content_type, encoding = mimetypes.guess_type(file['name'])
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    msg = MIMEBase(main_type, sub_type)

    msg.set_payload(file['data'].getvalue())
    encoders.encode_base64(msg)
    msg.add_header('Content-Disposition', 'attachment', filename=file['name'])
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(
            userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')


def download_file(service, file_id):
    file = service.files().get(fileId=file_id).execute()
    file_name = file.get('name')

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print("Download progress: {0}%".format(int(status.progress() * 100)))
    return {'name': file_name, 'data': fh}


def send_postweek_pre_email(week, type='post'):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=credentials)

    with open(f'../week{week}/week{week}{type}doc_id.txt', 'r') as file1:
        file_id = file1.readline().strip()
    file = download_file(drive_service, file_id)

    creds = None
    while not creds or not creds.valid:
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if creds.valid:
            creds.refresh(Request())
        else:
            print("Credentials are invalid or expired. Re-authentication is required.")
            flow = InstalledAppFlow.from_client_secrets_file(
                '../google-api/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print("New credentials have been obtained and saved.")

    service = build('gmail', 'v1', credentials=creds)
    with open('../utils/sender_email.txt', 'r') as file:
        for line in file:
            sender = line.strip()
    to = []
    with open('../utils/emails.txt', 'r') as file2:
        for line in file2:
            to.append(line.rstrip())
    if type == 'post':
        subject = f"Greenwood Picks Pool Week {week} Results and Standings"
    else:
        subject = f"Greenwood Picks Pool Week {week}"
    message_text = ""

    message = create_message_with_attachment(
        sender, to, subject, message_text, file)
    send_message(service, "me", message)


def create_message_link(sender, to, subject, message_text):
    message = MIMEMultipart()
    message['to'] = ', '.join(to)
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text, 'html')
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_preweek_form(week):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(
                "No valid credentials available. Please run the authentication script first.")
            exit()
    service = build('gmail', 'v1', credentials=creds)
    with open('../utils/sender_email.txt', 'r') as file:
        for line in file:
            sender = line.strip()
    to = []
    with open('../utils/emails.txt', 'r') as file2:
        for line in file2:
            to.append(line.rstrip())
    subject = f"Greenwood Week {week} Picks Pool Form"
    with open(f'../week{week}/form_id_{week}.json', 'r') as f:
        ids = json.load(f)
    form_id = ids['Form_Id']
    form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    message_text = f"Hello all, <br><br> Fill out this form: <a href='{form_url}'>Greenwood Week {week} Pick From</a>. <br><br> May The Best Man Win"
    message = create_message_link(sender, to, subject, message_text)
    send_message(service, "me", message)
