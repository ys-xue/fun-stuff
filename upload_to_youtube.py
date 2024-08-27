# Upload to youtube.

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

CLIENT_SECRETS_FILE = "/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/credentials2.json"

def authenticate_youtube():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8000)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

youtube = authenticate_youtube()

def parse_txt_file(txt_file_path):
    with open(txt_file_path, 'r') as file:
        lines = file.readlines()
    
    # Extract the creation time
    creation_time = None
    description = []
    for line in lines:
        line = line.strip()
        if line.startswith("- Creation Time (UTC):"):
            creation_time = line.split(":", 1)[1].strip()
        description.append(line)
    
    description_text = "\n".join(description)
    return creation_time, description_text

def upload_video(youtube, file_path, title, description, category="22", tags=None):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category
        },
        'status': {
            'privacyStatus': 'public',
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if 'id' in response:
            print(f"Video '{file_path}' uploaded successfully. Video ID: {response['id']}")
        elif 'error' in response:
            print(f"An error occurred: {response['error']['message']}")
        else:
            print("Uploading video...")

def upload_videos_in_folder(youtube, video_folder_path, txt_folder_path, uploaded_videos_file='uploaded_videos.json'):
    # Load the list of uploaded videos
    if os.path.exists(uploaded_videos_file):
        with open(uploaded_videos_file, 'r') as f:
            uploaded_videos = json.load(f)
    else:
        uploaded_videos = []

    upload_count = 0
    max_uploads = 80

    for file_name in os.listdir(video_folder_path):
        if file_name in uploaded_videos:
            print(f"Skipping {file_name}, already uploaded.")
            continue
        
        if upload_count >= max_uploads:
            print(f"Reached the upload limit of {max_uploads} videos.")
            break
        
        if file_name.endswith(('.mp4', '.avi', '.mov', '.mkv')):  # Add more extensions if needed
            file_path = os.path.join(video_folder_path, file_name)
            txt_file_name = file_name.rsplit('.', 1)[0] + ".txt"
            txt_file_path = os.path.join(txt_folder_path, txt_file_name)
            
            if os.path.exists(txt_file_path):
                title, description = parse_txt_file(txt_file_path)
                upload_video(youtube, file_path, title, description)
                uploaded_videos.append(file_name)
                upload_count += 1
                print(f"Uploaded {file_name}, total uploads: {upload_count}")
            else:
                print(f"Corresponding .txt file not found for {file_name}, skipping.")
    
    # Save the list of uploaded videos
    with open(uploaded_videos_file, 'w') as f:
        json.dump(uploaded_videos, f, indent=4)

    print(f"Finished uploading. {upload_count} videos uploaded.")



# Example usage
video_folder_path = "/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/downloads"
txt_folder_path = "/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/txt_descriptions"

upload_videos_in_folder(youtube, video_folder_path, txt_folder_path)