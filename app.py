import os
import requests
from flask import Flask, render_template, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

def authenticate_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def download_video(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return file_name

def upload_to_drive(file_name, credentials):
    service = build('drive', 'v3', credentials=credentials)
    file_metadata = {'name': os.path.basename(file_name)}
    media = MediaFileUpload(file_name, mimetype='video/mp4')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    url = request.form['url']
    if not url.startswith("http"):
        return "Invalid URL"
    file_name = 'downloaded_video.mp4'
    try:
        download_video(url, file_name)
        credentials = authenticate_drive()
        file_id = upload_to_drive(file_name, credentials)
        drive_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        os.remove(file_name)
        return f"Video uploaded successfully! <a href='{drive_link}' target='_blank'>Google Drive Link</a>"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
