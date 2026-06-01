"""
유튜브 화제 캐릭터 발굴
1. 유튜브 자동완성 API로 "캐릭터" 관련 급상승 검색어 수집
2. 추출된 캐릭터 이름으로 영상 조회수 측정
3. 화제성 순위 산출
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

# 자동완성 시드 키워드
SEED_QUERIES = [
    "캐릭터",
    "귀여운 캐릭터",
    "캐릭터 굿즈",
    "캐릭터 인형",
    "캐릭터 소개",
    "이모티콘 캐릭터",
]

# 노이즈 단어
NOISE = {
    "캐릭터", "귀여운", "굿즈", "인형", "소개", "이모티콘", "스티커",
    "만들기", "그리기", "그림", "뽑기", "추천", "순위", "모음", "종류",
    "귀여운것", "cute", "new", "신규", "출시", "레고", "블록",
    "게임", "스킨", "코스튬", "코스프레",
}


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브 자동완성 → 캐릭터 이름 추출 → 화제성 측정"""

    # 1단계: 자동완성으로 캐릭터 후보 수집
    print("   유튜브 자동완성으로 캐릭터 후보 수집 중...")
    candidates = _collect_character_candidates()
    print(f"   → 캐릭터 후보 {len(candidates)}개")

    if not candidates:
        return []

    # 2단계: 각 캐릭터 유튜브 조회수 측정
    print("   각 캐릭터 유튜브 화제성 측정 중...")
    results = []
    for char in candidates[:15]:  # 상위 15개만 측정
        score = _measure_character_buzz(char)
        time.sleep(random.uniform(0.8, 1.5))
        if score["total_views"] > 0:
            results.append(score)
            print(f"   {char}: {_fmt_views(score['total_views'])}")

    # 조회수 합산 기준 정렬
    results.sort(key=lambda x: x["total_views"], reverse=True)
    return results[:10]


def _collect_character_candidates() -> list[str]:
    """유튜브 자동완성 API에서 캐릭터 이름 추출"""
    seen = set()
    candidates = []

    for seed in SEED_QUERIES:
        suggestions = _get_autocomplete(seed)
        for s in suggestions:
            names = _extract_character_names(s)
            for name in names:
                if name not in seen and len(name) >= 2:
                    seen.add(name)
                    candidates.append(name)
        time.sleep(random.uniform(0.3, 0.7))

    return candidates


def _get_autocomplete(query: str) -> list[str]:
    """유튜브 자동완성 제안 목록 가져오기"""
    try:
        url = "https://suggestqueries.google.com/complete/search"
        params = {
            "client": "youtube",
            "q": query,
            "hl": "ko",
            "ds": "yt",
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
        # 응답: window.google.ac.h([...]) 형태
        text = resp.text
        # JSON 배열 추출
        match = re.search(r'\["([^"]+)"', text)
        if not match:
            return []
        # 전체 제안 목록 파싱
        start = text.find("[[")
        end = text.rfind("]]") + 2
        if start == -1:
            return []
        arr = json.loads(text[start:end])
        return [item[0] for item in arr if isinstance(item, list) and item]
    except Exception as e:
        print(f"   [자동완성] '{query}' 실패: {e}")
        return []


def _extract_character_names(suggestion: str) -> list[str]:
    """자동완성 문구에서 캐릭터 이름 추출"""
    s = suggestion.strip().lower()
    results = []

    # 노이즈 단어 제거 후 남은 단어가 캐릭터 이름 후보
    words = re.split(r"[\s\-\_]+", suggestion.strip())
    for word in words:
        w = word.strip()
        w_lower = w.lower()

        # 노이즈 제거
        if w_lower in NOISE or len(w) <= 1:
            continue
        # 숫자만
        if re.fullmatch(r"[\d]+", w):
            continue
        # 한글 2~8자 또는 영문 2~15자
        if re.fullmatch(r"[가-힣]{2,8}", w) or re.fullmatch(r"[A-Za-z][a-zA-Z]{1,14}", w):
            results.append(w)

    return results


def _measure_character_buzz(character: str) -> dict:
    """캐릭터 이름으로 유튜브 검색 → 상위 영상 조회수 합산"""
    try:
        query = f"{character} 캐릭터"
        encoded = quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"

        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()

        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return _empty(character)

        data = json.loads(match.group(1))
        videos = _parse_videos(data)

        if not videos:
            return _empty(character)

        total_views = sum(v["views"] for v in videos[:5])
        top_video = videos[0] if videos else {}

        return {
            "character":    character,
            "total_views":  total_views,
            "video_count":  len(videos),
            "top_title":    top_video.get("title", ""),
            "top_views":    top_video.get("views", 0),
            "top_thumb":    top_video.get("thumbnail", ""),
            "top_url":      top_video.get("url", ""),
        }
    except Exception:
        return _empty(character)


def _parse_videos(data: dict) -> list[dict]:
    videos = []
    try:
        contents = (
            data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
        )
        for section in contents:
            for item in section.get("itemSectionRenderer", {}).get("contents", []):
                v = item.get("videoRenderer", {})
                if not v:
                    continue
                title = _get_text(v.get("title", {}))
                vid   = v.get("videoId", "")
                views = _parse_views(_get_text(v.get("viewCountText", {})))
                thumbs = v.get("thumbnail", {}).get("thumbnails", [])
                thumb  = thumbs[-1].get("url", "") if thumbs else ""
                if title and vid:
                    videos.append({
                        "title":     title,
                        "views":     views,
                        "thumbnail": thumb,
                        "url":       f"https://www.youtube.com/watch?v={vid}",
                    })
                if len(videos) >= 10:
                    break
    except Exception:
        pass
    return videos


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


def _empty(char: str) -> dict:
    return {"character": char, "total_views": 0, "video_count": 0,
            "top_title": "", "top_views": 0, "top_thumb": "", "top_url": ""}


def _fmt_views(n: int) -> str:
    if n >= 100000000: return f"{n/100000000:.1f}억"
    if n >= 10000:     return f"{n/10000:.0f}만"
    if n >= 1000:      return f"{n/1000:.1f}천"
    return str(n) if n else "—"


def format_views(n: int) -> str:
    return _fmt_views(n)
