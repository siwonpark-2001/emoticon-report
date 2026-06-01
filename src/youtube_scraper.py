"""
유튜브 급상승 영상에서 캐릭터/이모티콘 관련 콘텐츠 수집
YouTube Innertube API (API 키 불필요)
"""
import re
import json
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/json",
}

# 캐릭터/이모티콘 관련 필터 키워드
CHARACTER_HINTS = [
    "이모티콘", "캐릭터", "스티커", "카카오", "라이언", "어피치", "춘식",
    "펭수", "죠르디", "루피", "무지", "콘", "제이지", "튜브", "프로도",
    "토끼", "고양이", "강아지", "곰", "햄스터", "오리", "개구리", "너구리",
    "뽀로로", "타요", "로보카폴리", "포켓몬", "짱구", "신비아파트",
    "귀여운", "cute", "chibi", "애니", "animation", "캐릭터굿즈",
]


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브 급상승(한국) 영상 중 캐릭터 관련 필터링"""
    videos = _fetch_trending_videos()
    if not videos:
        return []

    results = []
    for v in videos:
        title = v.get("title", "")
        channel = v.get("channel", "")
        combined = (title + " " + channel).lower()

        matched = [kw for kw in CHARACTER_HINTS if kw.lower() in combined]
        if not matched:
            continue

        results.append({
            "title": title,
            "channel": channel,
            "views": v.get("views", 0),
            "views_str": v.get("views_str", ""),
            "thumbnail": v.get("thumbnail", ""),
            "url": v.get("url", ""),
            "matched_keywords": matched[:3],
        })

    return results[:10]


def _fetch_trending_videos() -> list[dict]:
    """YouTube Innertube API로 한국 급상승 영상 수집"""
    try:
        # YouTube 내부 API — API 키 불필요
        url = "https://www.youtube.com/youtubei/v1/browse"
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101",
                    "hl": "ko",
                    "gl": "KR",
                }
            },
            "browseId": "FEtrending",
            "params": "4gINGgt5dG1hX2NoYXJ0cw%3D%3D",  # 한국 급상승
        }
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return _parse_innertube_response(data)

    except Exception as e:
        print(f"   [YouTube] Innertube API 실패: {e}, HTML 파싱 시도...")
        return _fetch_trending_html()


def _parse_innertube_response(data: dict) -> list[dict]:
    """Innertube 응답에서 영상 목록 추출"""
    videos = []
    try:
        # 응답 구조 탐색
        tabs = (data.get("contents", {})
                    .get("twoColumnBrowseResultsRenderer", {})
                    .get("tabs", []))
        for tab in tabs:
            tab_content = (tab.get("tabRenderer", {})
                              .get("content", {})
                              .get("sectionListRenderer", {})
                              .get("contents", []))
            for section in tab_content:
                items = (section.get("itemSectionRenderer", {})
                                .get("contents", []))
                for item in items:
                    shelf = item.get("shelfRenderer", {})
                    shelf_items = (shelf.get("content", {})
                                       .get("expandedShelfContentsRenderer", {})
                                       .get("items", []))
                    for si in shelf_items:
                        v = si.get("videoRenderer", {})
                        if not v:
                            continue
                        parsed = _parse_video_renderer(v)
                        if parsed:
                            videos.append(parsed)
    except Exception:
        pass
    return videos


def _parse_video_renderer(v: dict) -> dict | None:
    try:
        title = _get_text(v.get("title", {}))
        channel = _get_text(v.get("longBylineText", {}) or v.get("shortBylineText", {}))
        video_id = v.get("videoId", "")
        thumbnail = ""
        thumbs = v.get("thumbnail", {}).get("thumbnails", [])
        if thumbs:
            thumbnail = thumbs[-1].get("url", "")

        views_str = _get_text(v.get("viewCountText", {}))
        views = _parse_views(views_str)

        if not title or not video_id:
            return None

        return {
            "title": title,
            "channel": channel,
            "views": views,
            "views_str": views_str,
            "thumbnail": thumbnail,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
    except Exception:
        return None


def _fetch_trending_html() -> list[dict]:
    """HTML 페이지에서 초기 데이터 파싱 (fallback)"""
    try:
        resp = requests.get(
            "https://www.youtube.com/feed/trending?gl=KR&hl=ko",
            headers=HEADERS, timeout=15
        )
        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(1))
        return _parse_innertube_response(data)
    except Exception as e:
        print(f"   [YouTube] HTML 파싱도 실패: {e}")
        return []


def _get_text(obj: dict) -> str:
    if not obj:
        return ""
    if "simpleText" in obj:
        return obj["simpleText"]
    runs = obj.get("runs", [])
    return "".join(r.get("text", "") for r in runs)


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
