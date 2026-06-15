"""
YouTube OAuth2 refresh_token 발급 스크립트.
브라우저에서 Google 계정 로그인 → 허용 하면 refresh_token이 .env에 자동 저장됩니다.
"""
import os
import re
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

ENV_PATH = Path(__file__).parent / ".env"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://127.0.0.1:8080/"

load_dotenv(ENV_PATH)

client_config = {
    "web": {
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI],
    }
}

flow = Flow.from_client_config(client_config, SCOPES, redirect_uri=REDIRECT_URI)
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

print(f"\n브라우저가 열립니다. Google 계정으로 로그인 후 권한을 허용해주세요.\n")
print(f"자동으로 열리지 않으면 아래 URL을 브라우저에 붙여넣으세요:\n{auth_url}\n")
webbrowser.open(auth_url)

received_code = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        received_code = params.get("code")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h2>인증 완료! 이 창을 닫으셔도 됩니다.</h2>".encode("utf-8"))

    def log_message(self, *args):
        pass

server = HTTPServer(("127.0.0.1", 8080), Handler)
print("인증 대기 중...")
server.handle_request()

flow.fetch_token(code=received_code)
refresh_token = flow.credentials.refresh_token

print(f"\n[OK] refresh_token:\n{refresh_token}\n")

env_text = ENV_PATH.read_text(encoding="utf-8")
env_text = re.sub(
    r"^YOUTUBE_REFRESH_TOKEN=.*$",
    f"YOUTUBE_REFRESH_TOKEN={refresh_token}",
    env_text,
    flags=re.MULTILINE,
)
ENV_PATH.write_text(env_text, encoding="utf-8")
print(f"[OK] .env 저장 완료: {ENV_PATH}")
