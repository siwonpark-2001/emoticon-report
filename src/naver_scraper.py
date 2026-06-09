"""
네이버 데이터랩 캐릭터 검색트렌드
- 카카오 신규/인기 이모티콘 캐릭터명 + 고정 캐릭터 목록의 네이버 검색량 비교
- 이번 주 검색 관심도 점수(0~100) 측정 → 급상승 캐릭터 발굴
"""
import os
import requests
from datetime import datetime, timezone, timedelta

NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

KST = timezone(timedelta(hours=9))

HEADERS = {
    "X-Naver-Client-Id":     NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    "Content-Type":          "application/json",
}

# 항상 트래킹할 고정 캐릭터 목록
FIXED_CHARACTERS = [
    "라이언", "어피치", "춘식이", "죠르디", "잔망루피",
    "펭수", "뽀로로", "핑크퐁", "시나모롤", "쿠로미",
    "헬로키티", "포켓몬", "짱구", "스티치", "무지콘",
]


def fetch_naver_trending_characters(extra_keywords: list[str] = None) -> list[dict]:
    """
    캐릭터 키워드들의 네이버 검색트렌드 점수 측정
    extra_keywords: 카카오 신규 이모티콘에서 추출한 캐릭터명 등
    """
    if not NAVER_CLIENT_ID:
        print("   [Naver] API 키 없음 — 건너뜀")
        return []

    now   = datetime.now(KST)
    end   = now.strftime("%Y-%m-%d")
    start = (now - timedelta(days=28)).strftime("%Y-%m-%d")  # 최근 4주

    # 고정 + 추가 키워드 합산 (중복 제거)
    all_chars = list(FIXED_CHARACTERS)
    if extra_keywords:
        for kw in extra_keywords:
            if kw not in all_chars:
                all_chars.append(kw)
    all_chars = all_chars[:30]  # 최대 30개

    print(f"   네이버 검색트렌드 측정 대상: {len(all_chars)}개")

    results = _batch_search_trend(all_chars, start, end)

    # 이번 주 점수 높은 순 정렬
    results.sort(key=lambda x: x.get("this_week", 0), reverse=True)
    return results[:15]


def _batch_search_trend(keywords: list[str], start: str, end: str) -> list[dict]:
    """검색어트렌드 API — 5개씩 배치 처리"""
    url = "https://openapi.naver.com/v1/datalab/search"
    all_results = {}

    batch_size = 5
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i + batch_size]
        groups = [{"groupName": kw, "keywords": [kw]} for kw in batch]
        body = {
            "startDate":     start,
            "endDate":       end,
            "timeUnit":      "week",
            "keywordGroups": groups,
        }
        try:
            resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
            resp.raise_for_status()
            for item in resp.json().get("results", []):
                name = item.get("title", "")
                data = item.get("data", [])
                if not data:
                    continue
                # 가장 최근 주 점수
                this_week = data[-1].get("ratio", 0) if data else 0
                # 4주 평균
                avg = sum(d.get("ratio", 0) for d in data) / len(data)
                # 전주 대비 변화율
                prev_week = data[-2].get("ratio", 0) if len(data) >= 2 else 0
                change = this_week - prev_week

                all_results[name] = {
                    "keyword":   name,
                    "this_week": round(this_week, 1),
                    "avg":       round(avg, 1),
                    "change":    round(change, 1),
                    "weekly_data": [d.get("ratio", 0) for d in data],
                }
        except Exception as e:
            print(f"   [Naver] 배치 {i//batch_size+1} 실패: {e}")

    return list(all_results.values())


def _level(score: float) -> str:
    if score >= 60: return "🔥 급상승"
    if score >= 30: return "📈 상승"
    if score >= 10: return "😐 보통"
    if score >  0:  return "📉 낮음"
    return "—"
