import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
from googleapiclient.http import MediaIoBaseDownload
import requests
import json
from typing import List, Dict

# Define the OAuth 2.0 scope
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

def authenticate_google_photos() -> Credentials:
    """
    Authenticate and return the Google Photos service.

    Returns:
        Credentials: An authenticated Google Photos service instance.
    """
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/credentials2.json", SCOPES
            )
            creds = flow.run_local_server(port=8000)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("photoslibrary", "v1", credentials=creds, static_discovery=False)
    return service

def get_all_videos(service) -> List[Dict]:
    """
    Retrieve all video items from the user's Google Photos library.

    Args:
        service: The authenticated Google Photos service instance.

    Returns:
        List[Dict]: A list of dictionaries containing video metadata.
    """
    all_videos = []
    next_page_token = None

    while True:
        search_json = {
            "pageSize": 100,
            "filters": {
                "mediaTypeFilter": {
                    "mediaTypes": ["VIDEO"]
                }
            },
            "pageToken": next_page_token
        }

        # Make the request to the API
        results = service.mediaItems().search(body=search_json).execute()
        items = results.get('mediaItems', [])

        # Add the items from this page to the overall list
        all_videos.extend(items)

        # Check if there's a next page
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break  # No more pages

    return all_videos

def save_video(video_info: Dict) -> None:
    """
    Save the video and its metadata to the specified directory.

    Args:
        video_info (Dict): A dictionary containing video metadata.
    """
    # Extract the creation time
    creation_time = video_info["mediaMetadata"]["creationTime"]
    creation_time_filename = creation_time.replace(":", "-").replace("T", "_").replace("Z", "")

    # Download the video
    video_url = video_info["baseUrl"] + "=dv"
    video_response = requests.get(video_url, stream=True)

    # Save the video file
    video_filename = f"/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/downloads/{creation_time_filename}.mp4"
    with open(video_filename, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=8192):
            if chunk:  # Filter out keep-alive new chunks
                f.write(chunk)

    # Save the metadata to a JSON file
    metadata_filename = f"/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/downloads/{creation_time_filename}.json"
    with open(metadata_filename, "w") as json_file:
        json.dump(video_info, json_file, indent=4)

    print(f"Video saved as {video_filename}")
    print(f"Metadata saved as {metadata_filename}")

def main() -> None:
    """
    Main function to authenticate, retrieve all videos, and save them.
    """
    service = authenticate_google_photos()
    all_videos = get_all_videos(service)

    for video in all_videos:
        # Create the filename from the video's creation time
        video_filename = f"/Users/xueyishu/Documents/mavenGenAI/Lesson1/google_download/downloads/{video['mediaMetadata']['creationTime'].replace(':', '-').replace('T', '_').replace('Z', '')}.mp4"

        # Check if the file already exists
        if os.path.exists(video_filename):
            print(f"{video_filename} already exists. Skipping download.")
            continue  # Skip to the next iteration of the loop
        else:
            save_video(video)

if __name__ == "__main__":
    main()
