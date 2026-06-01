"""
유튜브 화제 캐릭터 영상 수집
YouTube 검색 결과에서 캐릭터 관련 최신 인기 영상 자동 발굴
API 키 불필요
"""
import re
import json
import time
import random
import requests
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 검색 쿼리 목록 (카카오와 무관한 독립적 캐릭터 탐색)
SEARCH_QUERIES = [
    "캐릭터 소개",
    "귀여운 캐릭터",
    "신규 캐릭터",
    "캐릭터 굿즈",
    "이모티콘 캐릭터",
]

# 캐릭터 관련 필터 키워드
CHARACTER_HINTS = [
    "캐릭터", "이모티콘", "스티커", "굿즈", "인형",
    "토끼", "고양이", "강아지", "곰", "햄스터", "오리", "개구리", "너구리", "펭귄",
    "냥", "댕", "뽀", "쨩", "롤링", "루피", "무지",
    "귀여운", "cute", "캐릭", "공개", "신규", "출시", "소개",
]


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브에서 캐릭터 관련 최신 인기 영상 수집"""
    all_videos = []
    seen_ids = set()

    for query in SEARCH_QUERIES:
        videos = _search_youtube(query)
        for v in videos:
            vid = v.get("video_id", "")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_videos.append(v)
        time.sleep(random.uniform(0.5, 1.2))

    # 조회수 높은 순 정렬
    all_videos.sort(key=lambda x: x.get("views", 0), reverse=True)
    return all_videos[:12]


def _search_youtube(query: str) -> list[dict]:
    """YouTube 검색 결과 스크래핑 (최근 1주일 필터)"""
    try:
        # sp 파라미터: 최근 1주일 내 업로드된 영상
        encoded = quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgQIARAB"

        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))
        return _parse_search_results(data, query)

    except Exception as e:
        print(f"   [YouTube] '{query}' 검색 실패: {e}")
        return []


def _parse_search_results(data: dict, query: str) -> list[dict]:
    results = []
    try:
        contents = (
            data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
        )
        for section in contents:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                v = item.get("videoRenderer", {})
                if not v:
                    continue
                parsed = _parse_video(v, query)
                if parsed:
                    results.append(parsed)
                if len(results) >= 8:
                    break
    except Exception:
        pass
    return results


def _parse_video(v: dict, query: str) -> dict | None:
    try:
        title   = _get_text(v.get("title", {}))
        channel = _get_text(v.get("longBylineText", {}) or v.get("shortBylineText", {}))
        vid     = v.get("videoId", "")
        if not title or not vid:
            return None

        # 캐릭터 관련 키워드 매칭
        combined = (title + " " + channel).lower()
        matched  = [kw for kw in CHARACTER_HINTS if kw.lower() in combined]
        if not matched:
            return None

        thumbs    = v.get("thumbnail", {}).get("thumbnails", [])
        thumbnail = thumbs[-1].get("url", "") if thumbs else ""
        views_str = _get_text(v.get("viewCountText", {}))
        views     = _parse_views(views_str)
        published = _get_text(v.get("publishedTimeText", {}))

        return {
            "title":            title,
            "channel":          channel,
            "video_id":         vid,
            "views":            views,
            "views_str":        views_str,
            "published":        published,
            "thumbnail":        thumbnail,
            "url":              f"https://www.youtube.com/watch?v={vid}",
            "matched_keywords": matched[:3],
            "search_query":     query,
        }
    except Exception:
        return None


def _get_text(obj: dict) -> str:
    if not obj:
        return ""
    if "simpleText" in obj:
        return obj["simpleText"]
    return "".join(r.get("text", "") for r in obj.get("runs", []))


def _parse_views(s: str) -> int:
    if not s:
        return 0
    nums = re.sub(r"[^\d]", "", s)
    return int(nums) if nums else 0


def format_views(n: int) -> str:
    if n >= 100000000:
        return f"{n/100000000:.1f}억"
    if n >= 10000:
        return f"{n/10000:.0f}만"
    if n >= 1000:
        return f"{n/1000:.1f}천"
    return str(n) if n else "—"
