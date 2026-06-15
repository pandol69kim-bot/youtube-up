"""
YouTube OAuth2 재인증 스크립트.

실행하면 브라우저 인증 URL을 출력한다.
URL 방문 후 리다이렉트된 URL(또는 코드)을 붙여 넣으면
새 refresh_token을 .env에 자동으로 업데이트한다.
"""

import os
import re
import sys
import urllib.parse
import urllib.request
import json
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # 콘솔 copy-paste 방식


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def update_env(env_path: Path, key: str, value: str) -> None:
    text = env_path.read_text(encoding="utf-8")
    pattern = rf"^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"
    new_text, n = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if n == 0:
        new_text = text.rstrip("\n") + f"\n{replacement}\n"
    env_path.write_text(new_text, encoding="utf-8")


def exchange_code(code: str, client_id: str, client_secret: str) -> dict:
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"

    if not env_path.exists():
        print(f"ERROR: .env 파일을 찾을 수 없습니다: {env_path}")
        sys.exit(1)

    env = load_env(env_path)
    client_id = env.get("YOUTUBE_CLIENT_ID", "")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("ERROR: .env에 YOUTUBE_CLIENT_ID 또는 YOUTUBE_CLIENT_SECRET가 없습니다.")
        sys.exit(1)

    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",  # 항상 새 refresh_token 발급
    })
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    print("=" * 60)
    print("아래 URL을 브라우저에서 열어 Google 계정으로 로그인하세요.")
    print("(YouTube 채널이 있는 계정이어야 합니다)")
    print("=" * 60)
    print(auth_url)
    print("=" * 60)
    print()

    code = input("인증 후 표시된 코드(또는 리다이렉트 URL)를 붙여 넣으세요:\n> ").strip()

    # 전체 URL이 붙여넣어진 경우 code= 파라미터만 추출
    if code.startswith("http"):
        parsed = urllib.parse.urlparse(code)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [code])[0]

    print()
    print("코드 교환 중...")
    try:
        tokens = exchange_code(code, client_id, client_secret)
    except Exception as e:
        print(f"ERROR: 토큰 교환 실패 — {e}")
        sys.exit(1)

    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        print("ERROR: refresh_token이 응답에 없습니다.")
        print("응답:", tokens)
        sys.exit(1)

    update_env(env_path, "YOUTUBE_REFRESH_TOKEN", refresh_token)
    print(f"YOUTUBE_REFRESH_TOKEN 업데이트 완료.")
    print(f"새 토큰: {refresh_token[:30]}...")
    print()
    print("이제 백엔드를 재시작하면 새 토큰이 적용됩니다.")


if __name__ == "__main__":
    main()
