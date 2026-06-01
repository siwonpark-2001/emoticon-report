"""
유튜브 화제 캐릭터 발굴 - 바텀업 방식
핵심 원리: 한국어 유튜브 제목은 "캐릭터명 + 행동/종류" 패턴
           → 제목 앞부분 추출 + 고조회수 영상에서 반복 등장 = 화제 캐릭터
"""
import re
import json
import time
import random
import requests
from collections import Counter, defaultdict
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 캐릭터 관련 검색어 (캐릭터명이 제목 앞에 오는 유형)
SEARCH_QUERIES = [
    "캐릭터 굿즈 하울",
    "캐릭터 인형 언박싱",
    "캐릭터 소개 쇼츠",
    "산리오 캐릭터",
    "카카오 캐릭터",
    "캐릭터 뽑기",
    "귀여운 캐릭터 굿즈",
    "캐릭터 신상",
]

# 캐릭터명이 아닌 "행동/콘텐츠 종류" 단어들 (제목 분리 기준)
ACTION_WORDS = {
    # 행동
    "굿즈", "인형", "하울", "언박싱", "소개", "뽑기", "만들기", "그리기",
    "리뷰", "추천", "모음", "정리", "모아봤", "먹방", "레시피", "케이크",
    "쿠키", "도시락", "간식", "챌린지", "댄스", "커버", "브이로그", "일상",
    "신상", "신제품", "컬렉션", "구매", "쇼핑", "가격", "리스트", "탑",
    "순위", "랭킹", "베스트", "색칠", "칠하기", "꾸미기", "따라하기",
    "방법", "쉽게", "빠르게", "간단히", "무료", "공개", "출시",
    "카드", "스티커", "키링", "파우치", "에코백", "쿠션", "담요",
    # 일반 명사
    "캐릭터", "이모티콘", "스티커", "피규어", "봉제", "인형",
    "쇼츠", "영상", "유튜브", "릴스", "틱톡",
    # 수식어
    "귀여운", "귀여워", "이쁜", "예쁜", "진짜", "완전", "너무",
    "새로운", "신규", "최신", "인기", "화제",
    # 영문
    "shorts", "review", "unboxing", "haul", "diy", "collection",
    "official", "cute", "new", "best", "top",
}

# 최소 조회수 기준 (이 이상인 영상만 사용)
MIN_VIEWS = 50000


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브 인기 영상 제목에서 캐릭터명 추출"""

    print("   유튜브 인기 캐릭터 영상 수집 중...")
    all_videos = []
    seen_ids = set()

    for query in SEARCH_QUERIES:
        videos = _search_youtube(query)
        for v in videos:
            if v["video_id"] not in seen_ids and v["views"] >= MIN_VIEWS:
                seen_ids.add(v["video_id"])
                all_videos.append(v)
        time.sleep(random.uniform(0.5, 1.0))

    print(f"   → {MIN_VIEWS//10000}만 이상 영상 {len(all_videos)}개 수집")

    if not all_videos:
        return []

    # 제목에서 캐릭터명 추출 및 집계
    char_views   = defaultdict(int)
    char_count   = Counter()
    char_samples = defaultdict(list)

    for v in all_videos:
        chars = _extract_character_from_title(v["title"])
        for ch in chars:
            char_count[ch] += 1
            char_views[ch] += v["views"]
            if len(char_samples[ch]) < 2:
                char_samples[ch].append(v["title"])

    # 2개 이상 영상에 등장한 캐릭터만
    results = [
        {
            "character":   ch,
            "video_count": char_count[ch],
            "total_views": char_views[ch],
            "samples":     char_samples[ch],
            "score":       char_views[ch] * char_count[ch],
        }
        for ch, cnt in char_count.items()
        if cnt >= 2
    ]

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


def _extract_character_from_title(title: str) -> list[str]:
    """
    제목 앞부분에서 캐릭터명 추출
    패턴: [캐릭터명] [행동/종류] ...
    """
    results = []

    # 공백/특수문자로 분리
    parts = re.split(r"[\s\|\-\[\]\(\)\/]+", title.strip())

    # 앞에서부터 ACTION_WORD 나오기 전까지가 캐릭터명 후보
    candidate_parts = []
    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue
        if part_clean.lower() in ACTION_WORDS or _is_action_word(part_clean):
            break
        candidate_parts.append(part_clean)

    if not candidate_parts:
        return []

    # 후보 파트들을 조합해서 캐릭터명 후보 생성
    # 1단어 후보
    for part in candidate_parts[:3]:
        if _is_valid_character_name(part):
            results.append(part)

    # 2단어 조합 (예: "잔망 루피" → "잔망루피")
    if len(candidate_parts) >= 2:
        combined = candidate_parts[0] + candidate_parts[1]
        if _is_valid_character_name(combined):
            results.append(combined)

    return list(set(results))


def _is_action_word(word: str) -> bool:
    """행동/상태를 나타내는 단어인지 판별"""
    w = word.lower()
    # 동사형 어미
    if re.search(r"(하기|하는|하울|하기|만들기|그리기|칠하기|꾸미기)$", w):
        return True
    # 영문 일반어
    if w in {"the", "a", "an", "is", "are", "with", "for", "of", "in"}:
        return True
    return False


def _is_valid_character_name(name: str) -> bool:
    """캐릭터 이름으로 유효한지 판별"""
    if not name or len(name) < 2:
        return False
    n = name.lower()

    # 노이즈 제거
    if n in ACTION_WORDS:
        return False
    # 숫자만
    if re.fullmatch(r"[\d\s]+", name):
        return False
    # 한글 2~8자
    if re.fullmatch(r"[가-힣]{2,8}", name):
        return True
    # 영문 2~20자 (브랜드명)
    if re.fullmatch(r"[A-Za-z][A-Za-z\d\s]{1,19}", name):
        return True
    # 한글+영문 혼합
    if re.search(r"[가-힣]", name) and len(name) >= 2:
        return True
    return False


def _search_youtube(query: str) -> list[dict]:
    """유튜브 검색 결과 수집"""
    try:
        url = f"https://www.youtube.com/results?search_query={quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()

        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))
        return _parse_videos(data)
    except Exception as e:
        print(f"   [YouTube] '{query}' 실패: {e}")
        return []


def _parse_videos(data: dict) -> list[dict]:
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
            for item in section.get("itemSectionRenderer", {}).get("contents", []):
                v = item.get("videoRenderer", {})
                if not v:
                    continue
                title   = _get_text(v.get("title", {}))
                vid     = v.get("videoId", "")
                views   = _parse_views(_get_text(v.get("viewCountText", {})))
                channel = _get_text(v.get("longBylineText", {}) or v.get("shortBylineText", {}))
                thumbs  = v.get("thumbnail", {}).get("thumbnails", [])
                thumb   = thumbs[-1].get("url", "") if thumbs else ""

                if title and vid:
                    results.append({
                        "title":     title,
                        "video_id":  vid,
                        "views":     views,
                        "channel":   channel,
                        "thumbnail": thumb,
                        "url":       f"https://www.youtube.com/watch?v={vid}",
                    })
    except Exception:
        pass
    return results


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
    if n >= 100000000: return f"{n/100000000:.1f}억"
    if n >= 10000:     return f"{n/10000:.0f}만"
    if n >= 1000:      return f"{n/1000:.1f}천"
    return str(n) if n else "—"
