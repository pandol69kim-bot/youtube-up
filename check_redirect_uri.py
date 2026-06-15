import os
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv(Path(__file__).parent / ".env")

client_config = {
    "installed": {
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
flow.redirect_uri = "http://localhost:8080/"

auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

import urllib.parse as up
parsed = up.urlparse(auth_url)
params = dict(up.parse_qsl(parsed.query))
print("redirect_uri 실제 요청값:", params.get("redirect_uri"))
print("client_id:", params.get("client_id", "")[:30] + "...")
