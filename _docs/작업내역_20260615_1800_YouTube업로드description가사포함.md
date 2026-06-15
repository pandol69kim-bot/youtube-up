# 작업 내역

- **날짜**: 2026-06-15 18:00
- **작업자**: Claude

## 작업 내용

YouTube 업로드 시 가사가 있는 트랙의 가사를 영상 description에 자동으로 포함시켰다.

## 변경된 파일

- `backend/app/routers/youtube.py`: `_build_description()` 함수 추가, `/upload` 엔드포인트에서 호출

## description 조합 구조

```
{사용자 입력 description}

【수록곡】
00:00 트랙1 - 아티스트
03:05 트랙2 - 아티스트

【가사】
▶ 트랙1 - 아티스트
가사 내용...

▶ 트랙2
가사 내용...
```

- 각 섹션은 조건부: base description이 비어 있으면 생략, 가사 없는 트랙은 가사 섹션에서 제외
- `video.chapters`를 재활용하여 타임스탬프 목록 생성 (이미 렌더링 시 계산된 값)
- `/publish` 엔드포인트는 `/upload`를 내부 호출하므로 동일하게 적용됨

## 검증

- video_id=7 기준 description 조합 확인: base/수록곡/가사 섹션 모두 정상 포함 (199자)
- 백엔드 재시작 후 API 정상 응답 확인
