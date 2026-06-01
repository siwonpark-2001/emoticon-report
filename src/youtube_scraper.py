"""
유튜브 캐릭터/이모티콘 관련 인기 영상 수집
YouTube 검색 RSS 피드 활용 (API 키 불필요)
"""
import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 검색할 캐릭터/이모티콘 키워드
SEARCH_QUERIES = [
    "카카오이모티콘 캐릭터",
    "이모티콘 캐릭터 귀여운",
    "카카오프렌즈",
    "인기 캐릭터",
]

CHARACTER_HINTS = [
    "이모티콘", "캐릭터", "스티커", "카카오", "라이언", "어피치", "춘식",
    "펭수", "죠르디", "루피", "무지", "콘", "제이지", "튜브", "프로도",
    "토끼", "고양이", "강아지", "곰", "햄스터", "오리", "개구리", "너구리",
    "뽀로로", "타요", "포켓몬", "짱구", "귀여운", "cute", "chibi", "캐릭터굿즈",
]


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브 캐릭터 관련 최신 인기 영상 수집"""
    results = []
    seen_ids = set()

    for query in SEARCH_QUERIES:
        videos = _search_youtube_rss(query)
        for v in videos:
            vid = v.get("video_id", "")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                results.append(v)
        time.sleep(0.5)

    # 조회수 높은 순 정렬
    results.sort(key=lambda x: x.get("views", 0), reverse=True)
    return results[:10]


def _search_youtube_rss(query: str) -> list[dict]:
    """YouTube 검색 결과 스크래핑 (search_query RSS)"""
    try:
        # YouTube 검색 RSS 피드
        url = "https://www.youtube.com/feeds/videos.xml"
        # 검색 파라미터로는 채널 RSS만 지원하므로, 검색 API를 직접 호출
        return _search_youtube_web(query)
    except Exception:
        return []


def _search_youtube_web(query: str) -> list[dict]:
    """YouTube 검색 페이지 스크래핑"""
    try:
        import json
        import urllib.parse

        encoded = urllib.parse.quote(query)
        # 최근 1주일 필터 (sp 파라미터)
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgQIARAB"

        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # ytInitialData JSON 추출
        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))
        return _parse_search_results(data, query)

    except Exception as e:
        print(f"   [YouTube] '{query}' 검색 실패: {e}")
        return []


def _parse_search_results(data: dict, query: str) -> list[dict]:
    """ytInitialData에서 영상 목록 추출"""
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
                if len(results) >= 5:
                    break
    except Exception:
        pass
    return results


def _parse_video(v: dict, query: str) -> dict | None:
    try:
        title = _get_text(v.get("title", {}))
        channel = _get_text(v.get("longBylineText", {}) or v.get("shortBylineText", {}))
        video_id = v.get("videoId", "")

        if not title or not video_id:
            return None

        # 캐릭터 관련 키워드 매칭
        combined = (title + " " + channel).lower()
        matched = [kw for kw in CHARACTER_HINTS if kw.lower() in combined]
        if not matched:
            return None

        # 썸네일
        thumbs = v.get("thumbnail", {}).get("thumbnails", [])
        thumbnail = thumbs[-1].get("url", "") if thumbs else ""

        # 조회수
        views_text = _get_text(v.get("viewCountText", {}))
        views = _parse_views(views_text)

        # 업로드 시점
        published = _get_text(v.get("publishedTimeText", {}))

        return {
            "title": title,
            "channel": channel,
            "video_id": video_id,
            "views": views,
            "views_str": views_text,
            "published": published,
            "thumbnail": thumbnail,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "matched_keywords": matched[:3],
            "search_query": query,
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
